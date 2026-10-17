"""
ECG Signal Preprocessor.

Normalizes, resamples, and sanitizes 1D ECG lead signals (187 samples standardized
to the MIT-BIH / PTB-DB benchmark format) for the 1D CNN model.
"""
import numpy as np
import pandas as pd
from typing import Union, List, Tuple
import io


class ECGPreprocessor:
    TARGET_LENGTH = 187  # Standard length matching MIT-BIH PhysioNet benchmark

    @staticmethod
    def normalize_signal(signal: np.ndarray) -> np.ndarray:
        """Min-max normalize waveform into [0, 1] range."""
        signal = np.nan_to_num(signal, nan=0.0, posinf=1.0, neginf=0.0)
        s_min = np.min(signal)
        s_max = np.max(signal)
        if s_max - s_min > 1e-6:
            return (signal - s_min) / (s_max - s_min)
        return np.zeros_like(signal)

    @classmethod
    def process_raw_lead(cls, raw_signal: Union[List[float], np.ndarray]) -> np.ndarray:
        """
        Pads or truncates raw lead signals to TARGET_LENGTH (187 points)
        and applies min-max normalization.
        """
        arr = np.array(raw_signal, dtype=np.float32)
        if len(arr) < cls.TARGET_LENGTH:
            # Zero-pad signal to target length
            padded = np.zeros(cls.TARGET_LENGTH, dtype=np.float32)
            padded[:len(arr)] = arr
            arr = padded
        elif len(arr) > cls.TARGET_LENGTH:
            # Evenly resample to target length
            indices = np.linspace(0, len(arr) - 1, cls.TARGET_LENGTH).astype(int)
            arr = arr[indices]
            
        norm = cls.normalize_signal(arr)
        return norm

    @classmethod
    def parse_uploaded_csv(cls, file_bytes: bytes) -> Tuple[np.ndarray, List[float]]:
        """
        Parses an uploaded ECG CSV or text file containing lead values.
        Returns:
            - processed_tensor: np.ndarray of shape (1, 1, 187) ready for 1D CNN
            - waveform_list: List[float] for frontend visualization
        """
        text = file_bytes.decode('utf-8', errors='ignore').strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        values = []
        # If single line with comma/tab/space delimiters
        if len(lines) == 1 or (len(lines) > 1 and len(lines[0].split(',')) > 10):
            row_items = re_split = [x.strip() for x in lines[0].replace(';', ',').split(',') if x.strip()]
            for item in row_items:
                try:
                    values.append(float(item))
                except ValueError:
                    continue
        else:
            # Multiple lines, each line is a sample point
            for line in lines:
                parts = [p.strip() for p in line.replace(';', ',').split(',') if p.strip()]
                for p in parts:
                    try:
                        values.append(float(p))
                    except ValueError:
                        continue
                        
        if not values:
            raise ValueError("No valid numerical ECG lead signal points could be parsed from upload.")
            
        # If the last value is a ground truth label (like in MIT-BIH dataset), strip it if > 187 values
        if len(values) == 188:
            values = values[:187]
            
        processed = cls.process_raw_lead(values)
        waveform = processed.tolist()
        tensor_input = processed.reshape(1, 1, cls.TARGET_LENGTH)
        return tensor_input, waveform
