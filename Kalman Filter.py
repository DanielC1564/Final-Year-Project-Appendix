import time
import numpy as np

class KalmanFilter:
    """
    A 4-state Kalman filter for tracking a 2D object's position and velocity.
    
    State vector: [x, y, vx, vy]
    Measurements: [x, y] (position only — velocity is inferred, not directly measured)
    """
    def __init__(self):
        #State Matrix: Inputted Values
        self.x = np.zeros(4) 

        #State Transition Matrix: How the system changes
        self.F = np.array([[1,0,0,0],
                           [0,1,0,0],
                           [0,0,1,0],
                           [0,0,0,1]])
        
        #Measurement Function: What values the sensor is reading 
        self.H = np.array([[1,0,0,0],
                           [0,1,0,0]])
        
        self.P = np.eye(4) * 200       #Initial state covariance: High uncertainty due to no prior knowledge of positions.
        self.R = np.eye(2) * 80        #Measurement noise: Higher values make the filter trust sensor readings less and smooth more aggressively. Tune up if the sensor is noisy; tune down to track fast movements.
        self.Q = np.eye(4) * 0.01      #Process Noise: Represents how much real world movement can deviate from the constant velocity model each frame

    def predict(self):

        self.x = self.F @ self.x                            #Project state: x = F*x 
        self.P = self.F @ self.P @ self.F.T + self.Q        #Grow uncertainty: P = F*P*F^T + Q

    def update(self, measurement):
        z = np.array(measurement)        #Places measurments into an matrix

        
        y = z - (self.H @ self.x)            #Innovation: Difference between what was measured and what was predicted

        S = self.H @ self.P @ self.H.T + self.R     #Innovation Covariance: Total uncertainty in the innovation
        
        # Added safety for singular matrix, prevents matrix algebra errors
        try:
            K = self.P @ self.H.T @ np.linalg.inv(S)
        except np.linalg.LinAlgError:
            return

        
        self.x = self.x + (K @ y)   #Update state estimate

        I = np.eye(4)               #Identity Matrix

        self.P = (I - (K @ self.H)) @ self.P    #Updated Uncertainty


class KalmanTracker:
        """
        Correct the prediction using a new sensor measurement.
        Skips the update silently if the innovation covariance S is singular
        (e.g. degenerate measurement geometry), to avoid crashing on bad frames.
        """
    def __init__(self, threshold = 5):
        self.k = KalmanFilter()         #Underlying filter: KalmanTracker adds gating and confirmation logic on top
        self.initiated = False          #Assign obstalce as not detected initially
        self.hit_streak = 0             #Initialize hit streak tracker
        self.threshold = threshold      #Define the hit threshold
        self.last_time = time.time()    #Define the time variable used to calculate dt
        
    def update(self, raw_x, raw_y):
        current_time = time.time()

        #First detection: seed the state directly instead of predicting, because there is no prior state to predict from yet.
        if not self.initiated:
            self.k.x = np.array([float(raw_x), float(raw_y), 0, 0])       # Assign inputs to the matrix
            self.initiated = True
            self.hit_streak = 1
            return raw_x, raw_y
            
        #Calculate dt
        dt = current_time - self.last_time
        self.last_time = current_time


        self.k.F[0, 2] = dt    #x += vx * dt
        self.k.F[1, 3] = dt    #y += vy * dt

        self.k.predict()
        
        #Gating: Rejects measurments that are too far away from predictions (likely noise or wrong object)
        dist = np.sqrt((self.k.x[0] - raw_x)**2 + (self.k.x[1] - raw_y)**2)

        startup = self.hit_streak < self.threshold      #Skip gating during warmup — early predictions aren't reliable enough to reject measurements.

        if dist < 800 or startup:
            self.k.update([raw_x, raw_y])       #Call the update functions with the inputs
            self.hit_streak += 1                
        else:
            # Decrement rather than reset: a single missed frame shouldn't immediately drop a well-established track
            self.hit_streak = max(0, self.hit_streak - 1)        
        
        return self.k.x[0], self.k.x[1]

    @property
    def is_confirmed(self):
        #True if target has been detected enough times to be trusted
        return self.hit_streak >= self.threshold

    def reset(self):
        #Called when target is permenantly lost; resets all states.
        self.initiated = False
        self.hit_streak = 0
