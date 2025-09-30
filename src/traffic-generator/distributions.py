import numpy as np
import random
import time
from typing import Callable

class TrafficDistributions:
    @staticmethod
    def constant_rate(rate: float = 1.0) -> Callable:
        """Distribución constante: misma tasa siempre"""
        def generator():
            return 1.0 / rate
        return generator

    @staticmethod
    def poisson_rate(avg_rate: float = 1.0) -> Callable:
        """Distribución Poisson: eventos raros con tasa promedio"""
        def generator():
            return np.random.exponential(1.0 / avg_rate)
        return generator

    @staticmethod
    def bursty_traffic(avg_rate: float = 1.0, burst_factor: float = 5.0) -> Callable:
        """Tráfico con ráfagas: periodos tranquilos y luego bursts"""
        def generator():
            if random.random() < 0.2:  # 20% probabilidad de burst
                return np.random.exponential(1.0 / (avg_rate * burst_factor))
            else:
                return np.random.exponential(1.0 / (avg_rate * 0.2))
        return generator
    
