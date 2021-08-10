import numpy as np
import cv2

# config
class GapAlignment():
    def __init__(self, 
                 STABLE_THRESHOLD = 25,
                 GLOBAL_IMAGE_CROP_OFFSET_X = 0.2,
                 GLOBAL_IMAGE_CROP_OFFSET_Y = 0.1,
                 HIST_DIFF_THRESHOLD = 2,
                 DEFAULT_HIST_LEVEL = 0,
                 MIN_PEAKS = 2,
                 ADDON_HIST_LEVEL = 2.5,
                 OUT_OF_CENTER_THRESHOLD = 0.5,
                 GLOBAL_WIDTH = 128,
                 GLOBAL_HEIGHT = 256):
        self.STABLE_THRESHOLD = STABLE_THRESHOLD
        self.GLOBAL_IMAGE_CROP_OFFSET_X = GLOBAL_IMAGE_CROP_OFFSET_X
        self.GLOBAL_IMAGE_CROP_OFFSET_Y = GLOBAL_IMAGE_CROP_OFFSET_Y
        self.DEFAULT_HIST_LEVEL = DEFAULT_HIST_LEVEL
        self.MIN_PEAKS = MIN_PEAKS
        self.ADDON_HIST_LEVEL = ADDON_HIST_LEVEL
        self.OUT_OF_CENTER_THRESHOLD = OUT_OF_CENTER_THRESHOLD
        self.HIST_DIFF_THRESHOLD = HIST_DIFF_THRESHOLD
        self.GLOBAL_WIDTH = GLOBAL_WIDTH
        self.GLOBAL_HEIGHT = GLOBAL_HEIGHT
        self.offset_removes_x = list(range(0, int(self.GLOBAL_WIDTH*self.GLOBAL_IMAGE_CROP_OFFSET_X))) + list(range(int(self.GLOBAL_WIDTH*(1-self.GLOBAL_IMAGE_CROP_OFFSET_X)), self.GLOBAL_WIDTH))
        self.offset_removes_y = list(range(0, int(self.GLOBAL_HEIGHT*self.GLOBAL_IMAGE_CROP_OFFSET_Y))) + list(range(int(self.GLOBAL_HEIGHT*(1-self.GLOBAL_IMAGE_CROP_OFFSET_Y)), self.GLOBAL_HEIGHT))

    def to_gray(self, img):
        _img = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2GRAY)
        return _img

    def ignore_background(self, img):
        try:
            std_by_yaxis = img.std(0)
            which_stable = list(np.where(std_by_yaxis<= self.STABLE_THRESHOLD)[0])
            which_stable = list(set(which_stable)-set(self.offset_removes_x))
            return which_stable
        except Exception as e:
            print(e)
            return e

    def img_hist(self, gray_img):
        try:
            _gray_img = gray_img.copy()
            where_gap = self.ignore_background(_gray_img)
            if len(where_gap)==0:
                where_gap = np.arange(self.GLOBAL_WIDTH)
            img_hist = _gray_img[:,where_gap].mean(1)
            hist_diff = np.diff(img_hist)
            hist_diff = (hist_diff-hist_diff.mean())/(hist_diff.std()+1e-6)
            peak = list(np.where(hist_diff>self.HIST_DIFF_THRESHOLD)[0])
            peak = np.array(list(set(peak)-set(self.offset_removes_y)))
            if len(peak)==0:
                peak = np.array([self.GLOBAL_HEIGHT//2-2, self.GLOBAL_HEIGHT//2-1])
            return img_hist, peak
        except Exception as e:
            print(e)
            return e

    def cropping(self, img):
        print(img.shape)
        gray_img = self.to_gray(img)
        hist, peaks = self.img_hist(gray_img)
        try:
            hist = (hist-hist.mean())/(hist.std()+1e-6)
            hist_peak_cross = []
            hist_level = self.DEFAULT_HIST_LEVEL
            while True:
                if np.sum(hist<hist_level)<self.MIN_PEAKS:
                    hist_level += self.ADDON_HIST_LEVEL
                else:
                    break
            for p in peaks:
                if hist[p]<hist_level:
                    hist_peak_cross.append(p)
            peak = np.array(hist_peak_cross)
            if len(peak)>0:
                center_y = int((peak.max()+peak.min())/2)
            else:
                peak = np.array([self.GLOBAL_HEIGHT//2-2, self.GLOBAL_HEIGHT//2-1])
                center_y = self.GLOBAL_HEIGHT//2
        
            if np.abs(center_y-self.GLOBAL_WIDTH)>self.GLOBAL_WIDTH*self.OUT_OF_CENTER_THRESHOLD:
                return None
        
            else:
                start_y = center_y-self.GLOBAL_WIDTH//2
                end_y = start_y+self.GLOBAL_WIDTH

                pad_top = -start_y
                pad_bottom = end_y-self.GLOBAL_HEIGHT
    
                if start_y>=0:
                    if end_y<=self.GLOBAL_HEIGHT:
                        cropped_img = img[start_y:end_y]
                    else:
                        cropped_img = cv2.copyMakeBorder(img.copy(), 0, pad_bottom, 0, 0, cv2.BORDER_CONSTANT, value = [0,0,0])[start_y:end_y]
                else:
                    if end_y<=self.GLOBAL_HEIGHT:
                        cropped_img = cv2.copyMakeBorder(img.copy(), pad_top, 0, 0, 0, cv2.BORDER_CONSTANT, value = [0,0,0])[0:w]
                    else:
                        cropped_img = cv2.copyMakeBorder(img.copy(), pad_top, pad_bottom, 0, 0, cv2.BORDER_CONSTANT, value = [0,0,0])
                cropped_img = cv2.resize(cropped_img, (self.GLOBAL_WIDTH, self.GLOBAL_WIDTH))
                return cropped_img.astype('uint8')
        except Exception as e:
            print(e)


def cropping_and_saving_images(images, gap_index):
    for i, image in enumerate(images):
        cv2.imwrite('./out/gap_{}_{}.png'.format(gap_index, i), cropping(image))
