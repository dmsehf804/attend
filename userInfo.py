

class UserInfo:
    def __init__(self, 
        user_id, 
        user_name, 
        palm_feature, 
        gap_feature_index_finger, 
        gap_feature_middle_finger,
        gap_feature_ring_finger,
        gap_feature_pinky_finger,model_version) -> None:
        
        self.user_id = user_id
        self.user_name = user_name
        self.palm_feature = palm_feature
        self.gap_feature_index_finger = gap_feature_index_finger
        self.gap_feature_middle_finger = gap_feature_middle_finger
        self.gap_feature_ring_finger = gap_feature_ring_finger
        self.gap_feature_pinky_finger = gap_feature_pinky_finger
        self.model_version = model_version

    def get_user_id(self):
        return self.user_id

    def get_user_name(self):
        return self.user_name
    
    def get_palm_feature(self):
        return self.palm_feature

    def get_gap_feature_index_finger(self):
        return self.gap_feature_index_finger

    def get_gap_feature_middle_finger(self):
        return self.gap_feature_middle_finger

    def get_gap_feature_ring_finger(self):
        return self.gap_feature_ring_finger

    def get_gap_feature_pinky_finger(self):
        return self.gap_feature_pinky_finger
        
    def get_model_version(self):
        return self.model_version
