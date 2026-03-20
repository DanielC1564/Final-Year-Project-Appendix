#Import Libraries
import cv2
import numpy as np

import pygame
import math
import time
from rd03d import RD03D
from Kalman import KalmanFilter, KalmanTracker

class RadarDisplay:
    def __init__(self, width=1200, height=900):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("mmWave Radar Display - Kalman Filtered")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.GREEN = (0, 255, 0)
        self.DARK_GREEN = (0, 100, 0)
        self.BRIGHT_GREEN = (0, 255, 100)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)
        self.WHITE = (255, 255, 255)
        self.GRAY = (128, 128, 128)
        
        # Radar settings
        self.info_panel_width = 200  
        self.radar_area_width = width - self.info_panel_width - 40  
        self.radar_area_height = height - 100  
        
        self.center_x = self.info_panel_width + self.radar_area_width // 2
        self.center_y = height - 80  
        
        max_radius_by_width = self.radar_area_width // 2 - 20
        max_radius_by_height = self.radar_area_height - 60  
        self.radar_radius = min(max_radius_by_width, max_radius_by_height)
        
        self.max_range = 2000  # Default to 2 meters for better view of 1500mm limit
        self.fov_angle = 120  
        
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        self.sweep_angle = 0
        self.sweep_speed = 2
        
    def set_max_range(self, range_meters):
        """Set the maximum range in meters"""
        self.max_range = range_meters * 1000
        
    def distance_to_pixels(self, distance_mm):
        """Convert distance in mm to pixel radius"""
        return int((distance_mm / self.max_range) * self.radar_radius)
    
    def angle_to_screen_angle(self, angle_deg):
        """Convert radar angle to screen angle (radar faces up)"""
        return -angle_deg + 90
    
    def polar_to_cartesian(self, distance_mm, angle_deg):
        """Convert polar coordinates to screen cartesian"""
        pixel_radius = self.distance_to_pixels(distance_mm)
        screen_angle = math.radians(self.angle_to_screen_angle(angle_deg))
        
        x = self.center_x + pixel_radius * math.cos(screen_angle)
        y = self.center_y - pixel_radius * math.sin(screen_angle)
        
        return int(x), int(y)
    
    def draw_range_arc(self, radius, start_angle, end_angle, color, width=1):
        if radius <= 0 or radius > self.radar_radius:
            return
            
        start_screen_angle = math.radians(self.angle_to_screen_angle(start_angle))
        end_screen_angle = math.radians(self.angle_to_screen_angle(end_angle))
        
        points = []
        angle_step = (end_screen_angle - start_screen_angle) / 50 
        
        for i in range(51): 
            angle = start_screen_angle + i * angle_step
            x = self.center_x + radius * math.cos(angle)
            y = self.center_y - radius * math.sin(angle)
            points.append((x, y))
        
        if len(points) > 1:
            pygame.draw.lines(self.screen, color, False, points, width)
    
    def draw_radar_background(self):
        self.screen.fill(self.BLACK)
        
        fov_half = self.fov_angle / 2
        max_range_meters = self.max_range / 1000
        
        if max_range_meters <= 5:
            range_intervals = list(range(1, int(max_range_meters) + 1))
        elif max_range_meters <= 10:
            range_intervals = list(range(2, int(max_range_meters) + 1, 2))
        else:
            range_intervals = list(range(5, int(max_range_meters) + 1, 5))
        
        for range_m in range_intervals:
            range_mm = range_m * 1000
            radius = self.distance_to_pixels(range_mm)
            if 0 < radius <= self.radar_radius:
                self.draw_range_arc(radius, -fov_half, fov_half, self.DARK_GREEN)
                
                label_angle = 0
                screen_angle = math.radians(self.angle_to_screen_angle(label_angle))
                label_x = self.center_x + (radius + 15) * math.cos(screen_angle)
                label_y = self.center_y - (radius + 15) * math.sin(screen_angle)
                
                label = self.small_font.render(f"{range_m}m", True, self.DARK_GREEN)
                label_rect = label.get_rect(center=(label_x, label_y))
                self.screen.blit(label, label_rect)
        
        for angle in [-fov_half, fov_half]:
            screen_angle = math.radians(self.angle_to_screen_angle(angle))
            end_x = self.center_x + self.radar_radius * math.cos(screen_angle)
            end_y = self.center_y - self.radar_radius * math.sin(screen_angle)
            pygame.draw.line(self.screen, self.GREEN, (self.center_x, self.center_y), (end_x, end_y), 2)
        
        for angle in range(-60, 61, 30):
            if abs(angle) <= fov_half and angle != 0:
                screen_angle = math.radians(self.angle_to_screen_angle(angle))
                end_x = self.center_x + self.radar_radius * math.cos(screen_angle)
                end_y = self.center_y - self.radar_radius * math.sin(screen_angle)
                pygame.draw.line(self.screen, self.DARK_GREEN, (self.center_x, self.center_y), (end_x, end_y), 1)
                
                label_x = self.center_x + (self.radar_radius + 25) * math.cos(screen_angle)
                label_y = self.center_y - (self.radar_radius + 25) * math.sin(screen_angle)
                label = self.small_font.render(f"{angle}°", True, self.DARK_GREEN)
                label_rect = label.get_rect(center=(label_x, label_y))
                self.screen.blit(label, label_rect)
        
        screen_angle = math.radians(self.angle_to_screen_angle(0))
        end_x = self.center_x + self.radar_radius * math.cos(screen_angle)
        end_y = self.center_y - self.radar_radius * math.sin(screen_angle)
        pygame.draw.line(self.screen, self.GREEN, (self.center_x, self.center_y), (end_x, end_y), 1)
        
        pygame.draw.circle(self.screen, self.GREEN, (self.center_x, self.center_y), 4)
        
        fov_half_rad = math.radians(fov_half)
        left_angle = math.radians(self.angle_to_screen_angle(-fov_half))
        right_angle = math.radians(self.angle_to_screen_angle(fov_half))
        
        arc_points = [(self.center_x, self.center_y)]
        for i in range(51):
            angle = left_angle + i * (right_angle - left_angle) / 50
            x = self.center_x + self.radar_radius * math.cos(angle)
            y = self.center_y - self.radar_radius * math.sin(angle)
            arc_points.append((x, y))
        arc_points.append((self.center_x, self.center_y))
        
        pygame.draw.polygon(self.screen, self.DARK_GREEN, arc_points, 1)
    
    def draw_sweep(self):
        fov_half = self.fov_angle / 2
        if abs(self.sweep_angle) <= fov_half:
            screen_angle = math.radians(self.angle_to_screen_angle(self.sweep_angle))
            
            for i in range(5):
                alpha_angle = self.sweep_angle - i * 3
                if abs(alpha_angle) <= fov_half:
                    alpha_screen_angle = math.radians(self.angle_to_screen_angle(alpha_angle))
                    alpha_end_x = self.center_x + self.radar_radius * math.cos(alpha_screen_angle)
                    alpha_end_y = self.center_y - self.radar_radius * math.sin(alpha_screen_angle)
                    
                    color_intensity = 255 - (i * 40)
                    if color_intensity > 0:
                        color = (0, color_intensity, 0)
                        pygame.draw.line(self.screen, color, (self.center_x, self.center_y), (alpha_end_x, alpha_end_y), max(1, 3-i))
        
        self.sweep_angle += self.sweep_speed
        if self.sweep_angle > fov_half:
            self.sweep_angle = -fov_half
    
    def draw_target(self, target, target_num):
        if target.distance > self.max_range:
            return  
            
        if abs(target.angle) > self.fov_angle / 2:
            return
            
        x, y = self.polar_to_cartesian(target.distance, target.angle)
        
        colors = [self.BRIGHT_GREEN, self.YELLOW, self.RED]
        color = colors[target_num % len(colors)]
        
        pygame.draw.circle(self.screen, color, (x, y), 8)
        pygame.draw.circle(self.screen, self.WHITE, (x, y), 8, 2)
        
        if abs(target.speed) > 1:  
            arrow_length = min(40, abs(target.speed) * 2)
            angle_rad = math.radians(self.angle_to_screen_angle(target.angle))
            
            if target.speed > 0:  
                arrow_end_x = x + arrow_length * math.cos(angle_rad)
                arrow_end_y = y - arrow_length * math.sin(angle_rad)
                arrow_color = self.RED
            else:  
                arrow_end_x = x - arrow_length * math.cos(angle_rad)
                arrow_end_y = y + arrow_length * math.sin(angle_rad)
                arrow_color = self.GREEN
                
            pygame.draw.line(self.screen, arrow_color, (x, y), (arrow_end_x, arrow_end_y), 3)
            
            arrow_angle = math.atan2(arrow_end_y - y, arrow_end_x - x)
            head_length = 10
            head1_x = arrow_end_x - head_length * math.cos(arrow_angle - 0.5)
            head1_y = arrow_end_y - head_length * math.sin(arrow_angle - 0.5)
            head2_x = arrow_end_x - head_length * math.cos(arrow_angle + 0.5)
            head2_y = arrow_end_y - head_length * math.sin(arrow_angle + 0.5)
            
            pygame.draw.polygon(self.screen, arrow_color, [(arrow_end_x, arrow_end_y), (head1_x, head1_y), (head2_x, head2_y)])
            
        label_text = f"T{target_num+1}"
        label = self.small_font.render(label_text, True, color)
        self.screen.blit(label, (x + 12, y - 12))
    
    def draw_info_panel(self, targets):
        panel_x = 10
        panel_y = 10
        
        panel_rect = pygame.Rect(5, 5, self.info_panel_width - 10, self.height - 10)
        pygame.draw.rect(self.screen, (20, 20, 20), panel_rect)
        pygame.draw.rect(self.screen, self.DARK_GREEN, panel_rect, 2)
        
        title = self.font.render("mmWave Radar", True, self.WHITE)
        self.screen.blit(title, (panel_x, panel_y))
        
        range_text = self.small_font.render(f"Max Range: {self.max_range/1000:.1f}m", True, self.GRAY)
        self.screen.blit(range_text, (panel_x, panel_y + 30))
        
        y_offset = 60
        active_targets = 0
        
        for i, target in enumerate(targets[:3]):
            if target and target.distance <= self.max_range and abs(target.angle) <= 60:
                active_targets += 1
                color = [self.BRIGHT_GREEN, self.YELLOW, self.RED][i]
                
                info_lines = [
                    f"Target {i+1}:",
                    f"  Distance: {target.distance:.0f}mm",
                    f"  Angle: {target.angle:.1f}°",
                    f"  Speed: {target.speed:.1f}cm/s",
                ]
                
                for j, line in enumerate(info_lines):
                    text_color = color if j == 0 else self.WHITE
                    text = self.small_font.render(line, True, text_color)
                    self.screen.blit(text, (panel_x, panel_y + y_offset + j * 18))
                
                y_offset += 120
                
        if active_targets == 0:
            no_targets = self.small_font.render("No targets detected", True, self.GRAY)
            self.screen.blit(no_targets, (panel_x, panel_y + y_offset))
            
        legend_y = self.height - 140
        legend_title = self.small_font.render("Speed Legend:", True, self.WHITE)
        self.screen.blit(legend_title, (panel_x, legend_y))
        
        pygame.draw.line(self.screen, self.RED, (panel_x, legend_y + 25), (panel_x + 30, legend_y + 25), 3)
        pygame.draw.polygon(self.screen, self.RED, [(panel_x + 30, legend_y + 25), (panel_x + 25, legend_y + 20), (panel_x + 25, legend_y + 30)])
        away_text = self.small_font.render("Moving Away", True, self.WHITE)
        self.screen.blit(away_text, (panel_x + 40, legend_y + 20))
        
        pygame.draw.line(self.screen, self.GREEN, (panel_x, legend_y + 45), (panel_x + 30, legend_y + 45), 3)
        pygame.draw.polygon(self.screen, self.GREEN, [(panel_x, legend_y + 45), (panel_x + 5, legend_y + 40), (panel_x + 5, legend_y + 50)])
        toward_text = self.small_font.render("Moving Toward", True, self.WHITE)
        self.screen.blit(toward_text, (panel_x + 40, legend_y + 40))

class FilteredTarget:
    #Turn Cartesian Coordinates Back into Polar for use in the visualization
    def __init__(self, x, y, original_target):
        self.x = x
        self.y = y
        self.distance = math.hypot(x, y)
        self.angle = math.degrees(math.atan2(x, y)) if self.distance > 0 else 0
        self.speed = original_target.speed

def main():
    # Initialize radar
    radar = RD03D()
    radar.set_multi_mode(True) 
    # Initialize display
    display = RadarDisplay(1200, 800)
    display.set_max_range(7)

    # --- VIDEO RECORDER SETUP ---
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    video = cv2.VideoWriter("Radar_Kalman.mp4",fourcc,30,(display.width, display.height))
    
    # Initialize trackers
    t = {1: KalmanTracker(), 2: KalmanTracker(), 3: KalmanTracker()}
    
    clock = pygame.time.Clock()
    
    print("Kalman-Filtered Radar visualization started. Close window to exit.")
    
    try:
        running = True
        while running:
            # Handle PyGame Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # Pull new radar data
            radar.update()
            
            # Draw radar backgrounds
            display.draw_radar_background()
            display.draw_sweep()
            
            display_targets = [None, None, None]
            
            # Process & Filter Targets
            for i in range(1, 4):
                target = radar.get_target(i)
                
                if target and target.distance > 0:
                    # Apply the user-defined distance bounds
                    if 350 < target.distance < 6500:
                        x, y = t[i].update(target.x, target.y)
                        if t[i].is_confirmed:
                            # Package the filtered data for visualization
                            filtered_target = FilteredTarget(x, y, target)
                            display_targets[i-1] = filtered_target
                            display.draw_target(filtered_target, i-1)
                    else:
                        t[i].hit_streak = max(0, t[i].hit_streak - 1)
                else:
                    t[i].reset()
            
            display.draw_info_panel(display_targets)
            
            pygame.display.flip()
          
            # --- RECORD FRAME ---
            frame = pygame.surfarray.array3d(display.screen)    #Assign Frame
            frame = np.transpose(frame, (1, 0, 2))   #Rotate axes for OpenCV
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  #Match Colours 
            video.write(frame)    #Record Frame

            clock.tick(30)
            
    except KeyboardInterrupt:
        pass
    finally:
        radar.close()
        pygame.quit()
        video.release()   # release recorder
        print("Radar visualization stopped.")

if __name__ == "__main__":
    main()
