"""
Multi-Strategy Scorer

Combines signals from multiple trading strategies with weighted scoring.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.models.data_models import Signal, SignalType, CompositeSignal
from src.models.exceptions import StrategyError


class MultiStrategyScorer:
    """Multi-strategy scorer for combining signals with weighted scoring."""
    
    def __init__(self, strategy_weights: Optional[Dict[str, float]] = None):
        """
        Initialize multi-strategy scorer.
        
        Args:
            strategy_weights: Dictionary of strategy names and their weights
                            If None, equal weighting will be used
        """
        self.logger = logging.getLogger(__name__)
        self.strategy_weights = strategy_weights or {}
        self.default_weight = 1.0
    
    def calculate_composite_score(self, signals: List[Signal], 
                                symbol: str = "UNKNOWN") -> CompositeSignal:
        """
        Calculate weighted composite score from multiple strategy signals.
        
        Args:
            signals: List of Signal objects from different strategies
            symbol: Stock symbol for the composite signal
            
        Returns:
            CompositeSignal with weighted composite score
            
        Raises:
            StrategyError: If calculation fails
        """
        try:
            if not signals:
                raise StrategyError("No signals provided for composite scoring")
            
            # Filter out NO_SIGNAL entries for scoring
            active_signals = [s for s in signals if s.signal_type != SignalType.NO_SIGNAL]
            
            if not active_signals:
                # All signals are NO_SIGNAL
                return CompositeSignal(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    signal_type=SignalType.NO_SIGNAL,
                    composite_score=0.0,
                    confidence=0.0,
                    contributing_signals=signals,
                    strategy_weights=self._get_effective_weights(signals)
                )
            
            # Calculate weighted composite score
            total_weighted_score = 0.0
            total_weight = 0.0
            effective_weights = self._get_effective_weights(signals)
            
            for signal in active_signals:
                strategy_name = signal.strategy_name
                weight = effective_weights.get(strategy_name, self.default_weight)
                
                # Normalize signal to -100 to +100 scale
                normalized_score = self.normalize_signal_strength(signal)
                
                # Apply weight
                weighted_score = normalized_score * weight
                total_weighted_score += weighted_score
                total_weight += weight
            
            # Calculate final composite score
            if total_weight > 0:
                composite_score = total_weighted_score / total_weight
            else:
                composite_score = 0.0
            
            # Determine composite signal type and confidence
            signal_type, confidence = self._determine_composite_signal_type(
                composite_score, active_signals
            )
            
            return CompositeSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                signal_type=signal_type,
                composite_score=composite_score,
                confidence=confidence,
                contributing_signals=signals,
                strategy_weights=effective_weights
            )
            
        except Exception as e:
            raise StrategyError(f"Composite score calculation failed: {e}")
    
    def normalize_signal_strength(self, signal: Signal) -> float:
        """
        Normalize individual signal strength to -100 to +100 scale.
        
        Args:
            signal: Signal object to normalize
            
        Returns:
            Normalized signal strength (-100 to +100)
        """
        try:
            if signal.signal_type == SignalType.BUY:
                return signal.confidence * 100
            elif signal.signal_type == SignalType.SELL:
                return -signal.confidence * 100
            else:  # NO_SIGNAL
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Signal normalization failed: {e}")
            return 0.0
    
    def _determine_composite_signal_type(self, composite_score: float, 
                                       signals: List[Signal]) -> tuple:
        """
        Determine final signal type based on composite score and thresholds.
        
        Args:
            composite_score: Calculated composite score
            signals: List of contributing signals
            
        Returns:
            Tuple of (SignalType, confidence)
        """
        try:
            # Default thresholds (can be made configurable)
            strong_buy_threshold = 60.0
            buy_threshold = 30.0
            sell_threshold = -30.0
            strong_sell_threshold = -60.0
            
            # Calculate confidence based on signal agreement and strength
            avg_confidence = sum(s.confidence for s in signals) / len(signals) if signals else 0.0
            score_strength = abs(composite_score) / 100.0
            
            # Combine average confidence with score strength
            confidence = min(1.0, (avg_confidence + score_strength) / 2)
            
            # Determine signal type
            if composite_score >= strong_buy_threshold:
                return SignalType.BUY, min(0.9, confidence + 0.2)
            elif composite_score >= buy_threshold:
                return SignalType.BUY, confidence
            elif composite_score <= strong_sell_threshold:
                return SignalType.SELL, min(0.9, confidence + 0.2)
            elif composite_score <= sell_threshold:
                return SignalType.SELL, confidence
            else:
                return SignalType.NO_SIGNAL, 0.0
                
        except Exception as e:
            self.logger.error(f"Signal type determination failed: {e}")
            return SignalType.NO_SIGNAL, 0.0
    
    def _get_effective_weights(self, signals: List[Signal]) -> Dict[str, float]:
        """
        Get effective weights for all strategies in signals.
        
        Args:
            signals: List of signals from different strategies
            
        Returns:
            Dictionary of strategy names and their effective weights
        """
        try:
            strategy_names = set(signal.strategy_name for signal in signals)
            effective_weights = {}
            
            for strategy_name in strategy_names:
                if strategy_name in self.strategy_weights:
                    effective_weights[strategy_name] = self.strategy_weights[strategy_name]
                else:
                    effective_weights[strategy_name] = self.default_weight
            
            return effective_weights
            
        except Exception as e:
            self.logger.error(f"Weight calculation failed: {e}")
            return {signal.strategy_name: self.default_weight for signal in signals}
    
    def set_strategy_weights(self, weights: Dict[str, float]) -> None:
        """
        Set strategy weights.
        
        Args:
            weights: Dictionary of strategy names and weights
            
        Raises:
            StrategyError: If weights are invalid
        """
        try:
            # Validate weights
            for strategy_name, weight in weights.items():
                if not isinstance(weight, (int, float)):
                    raise StrategyError(f"Weight for {strategy_name} must be a number")
                if weight <= 0:
                    raise StrategyError(f"Weight for {strategy_name} must be positive")
            
            self.strategy_weights = weights.copy()
            self.logger.info(f"Updated strategy weights: {self.strategy_weights}")
            
        except Exception as e:
            raise StrategyError(f"Failed to set strategy weights: {e}")
    
    def get_strategy_weights(self) -> Dict[str, float]:
        """
        Get current strategy weights.
        
        Returns:
            Dictionary of strategy weights
        """
        return self.strategy_weights.copy()
    
    def add_strategy_weight(self, strategy_name: str, weight: float) -> None:
        """
        Add or update weight for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy
            weight: Weight value (must be positive)
            
        Raises:
            StrategyError: If weight is invalid
        """
        try:
            if not isinstance(weight, (int, float)):
                raise StrategyError("Weight must be a number")
            if weight <= 0:
                raise StrategyError("Weight must be positive")
            
            self.strategy_weights[strategy_name] = weight
            self.logger.debug(f"Set weight for {strategy_name}: {weight}")
            
        except Exception as e:
            raise StrategyError(f"Failed to add strategy weight: {e}")
    
    def remove_strategy_weight(self, strategy_name: str) -> None:
        """
        Remove weight for a specific strategy (will use default weight).
        
        Args:
            strategy_name: Name of the strategy to remove
        """
        if strategy_name in self.strategy_weights:
            del self.strategy_weights[strategy_name]
            self.logger.debug(f"Removed weight for {strategy_name}")
    
    def calculate_strategy_contribution(self, composite_signal: CompositeSignal) -> Dict[str, Dict]:
        """
        Calculate detailed contribution of each strategy to the composite signal.
        
        Args:
            composite_signal: CompositeSignal to analyze
            
        Returns:
            Dictionary with detailed contribution analysis
        """
        try:
            contributions = {}
            total_weight = sum(composite_signal.strategy_weights.values())
            
            for signal in composite_signal.contributing_signals:
                strategy_name = signal.strategy_name
                weight = composite_signal.strategy_weights.get(strategy_name, self.default_weight)
                normalized_weight = weight / total_weight if total_weight > 0 else 0
                
                # Calculate individual contribution
                signal_score = self.normalize_signal_strength(signal)
                weighted_contribution = signal_score * normalized_weight
                
                contributions[strategy_name] = {
                    'signal_type': signal.signal_type.value,
                    'confidence': signal.confidence,
                    'signal_score': signal_score,
                    'weight': weight,
                    'normalized_weight': normalized_weight,
                    'weighted_contribution': weighted_contribution,
                    'contribution_percentage': (weighted_contribution / composite_signal.composite_score * 100) if composite_signal.composite_score != 0 else 0
                }
            
            return contributions
            
        except Exception as e:
            self.logger.error(f"Strategy contribution calculation failed: {e}")
            return {}
    
    def get_signal_agreement_score(self, signals: List[Signal]) -> float:
        """
        Calculate agreement score between signals (0.0 to 1.0).
        
        Args:
            signals: List of signals to analyze
            
        Returns:
            Agreement score (higher = more agreement)
        """
        try:
            if len(signals) < 2:
                return 1.0  # Perfect agreement with single signal
            
            # Count signal types
            buy_count = sum(1 for s in signals if s.signal_type == SignalType.BUY)
            sell_count = sum(1 for s in signals if s.signal_type == SignalType.SELL)
            no_signal_count = sum(1 for s in signals if s.signal_type == SignalType.NO_SIGNAL)
            
            total_signals = len(signals)
            
            # Calculate agreement as the proportion of the majority signal type
            max_agreement = max(buy_count, sell_count, no_signal_count)
            agreement_score = max_agreement / total_signals
            
            return agreement_score
            
        except Exception as e:
            self.logger.error(f"Agreement score calculation failed: {e}")
            return 0.0
    
    def validate_signals(self, signals: List[Signal]) -> bool:
        """
        Validate that signals are suitable for composite scoring.
        
        Args:
            signals: List of signals to validate
            
        Returns:
            True if signals are valid, False otherwise
        """
        try:
            if not signals:
                return False
            
            # Check for duplicate strategies
            strategy_names = [signal.strategy_name for signal in signals]
            if len(strategy_names) != len(set(strategy_names)):
                self.logger.warning("Duplicate strategies found in signals")
                return False
            
            # Validate individual signals
            for signal in signals:
                if not isinstance(signal, Signal):
                    return False
                if not signal.strategy_name:
                    return False
                if not 0.0 <= signal.confidence <= 1.0:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Signal validation failed: {e}")
            return False