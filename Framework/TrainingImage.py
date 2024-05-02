from Framework.ImageCategory import ImageCategory

class TrainingImage():
    
    def __init__(self, filePath, imageCategory: ImageCategory):
        self.filePath = filePath
        self.imageCategory = imageCategory