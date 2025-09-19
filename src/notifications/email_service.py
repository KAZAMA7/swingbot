"""
Email Notification Service

Handles email notifications for trading signals.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Union, Tuple
from datetime import datetime

from src.models.data_models import Signal, CompositeSignal, SignalType
from src.models.exceptions import TradingBotError


class EmailNotificationError(TradingBotError):
    """Email notification specific errors."""
    pass


class EmailNotificationService:
    """Email notification service for trading signals."""
    
    def __init__(self, smtp_config: Dict):
        """
        Initialize email notification service.
        
        Args:
            smtp_config: SMTP configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.smtp_config = smtp_config
        self.enabled = smtp_config.get('enabled', False)
        
        if self.enabled:
            if not self.validate_smtp_config(smtp_config):
                raise EmailNotificationError("Invalid SMTP configuration")
    
    def send_signal_notification(self, signal: Union[Signal, CompositeSignal], 
                               symbol: str) -> bool:
        """
        Send email notification for trading signal.
        
        Args:
            signal: Signal or CompositeSignal to notify about
            symbol: Stock symbol
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self.enabled:
                self.logger.debug("Email notifications disabled, skipping")
                return True
            
            # Check if signal meets notification criteria
            if not self._should_send_notification(signal):
                self.logger.debug(f"Signal for {symbol} does not meet notification criteria")
                return True
            
            # Format email content
            subject, body = self.format_signal_email(signal, symbol)
            
            # Send email
            return self._send_email(subject, body)
            
        except Exception as e:
            self.logger.error(f"Failed to send signal notification for {symbol}: {e}")
            return False
    
    def format_signal_email(self, signal: Union[Signal, CompositeSignal], 
                          symbol: str) -> Tuple[str, str]:
        """
        Format email subject and body for signal notification.
        
        Args:
            signal: Signal or CompositeSignal to format
            symbol: Stock symbol
            
        Returns:
            Tuple of (subject, body)
        """
        try:
            timestamp = signal.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            if isinstance(signal, CompositeSignal):
                return self._format_composite_signal_email(signal, symbol, timestamp)
            else:
                return self._format_single_signal_email(signal, symbol, timestamp)
                
        except Exception as e:
            self.logger.error(f"Email formatting failed: {e}")
            return f"Trading Signal Alert - {symbol}", f"Error formatting signal details: {e}"
    
    def _format_composite_signal_email(self, signal: CompositeSignal, 
                                     symbol: str, timestamp: str) -> Tuple[str, str]:
        """Format email for composite signal."""
        signal_type_text = {
            SignalType.BUY: "🟢 BUY",
            SignalType.SELL: "🔴 SELL",
            SignalType.NO_SIGNAL: "⚪ NO SIGNAL"
        }
        
        signal_emoji = signal_type_text.get(signal.signal_type, "⚪")
        
        # Subject
        subject = f"{signal_emoji} Multi-Strategy Alert: {symbol} - Score: {signal.composite_score:.1f}"
        
        # Body
        body = f"""
🎯 MULTI-STRATEGY TRADING ALERT

📊 Symbol: {symbol}
📅 Time: {timestamp}
🎯 Signal: {signal.signal_type.value}
📈 Composite Score: {signal.composite_score:.1f}/100
🎪 Confidence: {signal.confidence:.1%}
🔢 Strategies: {signal.get_strategy_count()}

📋 STRATEGY BREAKDOWN:
"""
        
        # Add strategy breakdown
        breakdown = signal.get_signal_breakdown()
        for strategy_name, details in breakdown.items():
            body += f"""
  🔸 {strategy_name.upper()}:
     Signal Score: {details['signal_score']:.1f}
     Weight: {details['weight']:.1f}
     Contribution: {details['weighted_contribution']:.1f}
     Confidence: {details['confidence']:.1%}
"""
        
        # Add individual signal details
        body += "\n📊 INDIVIDUAL SIGNALS:\n"
        for i, individual_signal in enumerate(signal.contributing_signals, 1):
            if individual_signal.signal_type != SignalType.NO_SIGNAL:
                body += f"""
  {i}. {individual_signal.strategy_name.upper()}:
     Type: {individual_signal.signal_type.value}
     Confidence: {individual_signal.confidence:.1%}
"""
                
                # Add strategy-specific details
                if hasattr(individual_signal, 'indicators') and individual_signal.indicators:
                    body += "     Details: "
                    details = []
                    for key, value in individual_signal.indicators.items():
                        if isinstance(value, (int, float)):
                            details.append(f"{key}: {value:.2f}")
                        else:
                            details.append(f"{key}: {value}")
                    body += ", ".join(details[:3])  # Limit to first 3 details
                    body += "\n"
        
        body += f"""
⚠️  DISCLAIMER: This is an automated trading signal for informational purposes only. 
    Always conduct your own research before making investment decisions.

📧 Generated by Enhanced NIFTY Trading Bot
"""
        
        return subject, body
    
    def _format_single_signal_email(self, signal: Signal, symbol: str, 
                                  timestamp: str) -> Tuple[str, str]:
        """Format email for single strategy signal."""
        signal_type_text = {
            SignalType.BUY: "🟢 BUY",
            SignalType.SELL: "🔴 SELL",
            SignalType.NO_SIGNAL: "⚪ NO SIGNAL"
        }
        
        signal_emoji = signal_type_text.get(signal.signal_type, "⚪")
        
        # Subject
        subject = f"{signal_emoji} {signal.strategy_name.upper()} Alert: {symbol}"
        
        # Body
        body = f"""
🎯 TRADING SIGNAL ALERT

📊 Symbol: {symbol}
📅 Time: {timestamp}
🎯 Signal: {signal.signal_type.value}
📈 Strategy: {signal.strategy_name.upper()}
🎪 Confidence: {signal.confidence:.1%}

📋 SIGNAL DETAILS:
"""
        
        # Add strategy-specific details
        if hasattr(signal, 'indicators') and signal.indicators:
            for key, value in signal.indicators.items():
                if isinstance(value, (int, float)):
                    body += f"  🔸 {key.replace('_', ' ').title()}: {value:.2f}\n"
                else:
                    body += f"  🔸 {key.replace('_', ' ').title()}: {value}\n"
        
        body += f"""
⚠️  DISCLAIMER: This is an automated trading signal for informational purposes only. 
    Always conduct your own research before making investment decisions.

📧 Generated by Enhanced NIFTY Trading Bot
"""
        
        return subject, body
    
    def _should_send_notification(self, signal: Union[Signal, CompositeSignal]) -> bool:
        """
        Check if signal meets notification criteria.
        
        Args:
            signal: Signal to check
            
        Returns:
            True if notification should be sent
        """
        try:
            # Don't send for NO_SIGNAL
            if signal.signal_type == SignalType.NO_SIGNAL:
                return False
            
            # Check configuration settings
            send_on_strong_only = self.smtp_config.get('send_on_strong_signals_only', True)
            
            if send_on_strong_only:
                # Only send for high-confidence signals
                min_confidence = 0.6
                if isinstance(signal, CompositeSignal):
                    min_score = 50.0  # Minimum composite score
                    return signal.confidence >= min_confidence and abs(signal.composite_score) >= min_score
                else:
                    return signal.confidence >= min_confidence
            
            # Send all signals if not restricted to strong signals only
            return True
            
        except Exception as e:
            self.logger.error(f"Notification criteria check failed: {e}")
            return False
    
    def _send_email(self, subject: str, body: str) -> bool:
        """
        Send email using SMTP.
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Get SMTP configuration
            smtp_host = self.smtp_config['smtp_host']
            smtp_port = self.smtp_config['smtp_port']
            username = self.smtp_config['username']
            password = self.smtp_config['password']
            use_tls = self.smtp_config.get('use_tls', True)
            recipients = self.smtp_config.get('recipients', [])
            
            if not recipients:
                self.logger.warning("No email recipients configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(smtp_host, smtp_port)
            
            if use_tls:
                server.starttls()
            
            server.login(username, password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(username, recipients, text)
            server.quit()
            
            self.logger.info(f"Email notification sent successfully to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def validate_smtp_config(self, config: Dict) -> bool:
        """
        Validate SMTP configuration settings.
        
        Args:
            config: SMTP configuration dictionary
            
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            required_fields = ['smtp_host', 'smtp_port', 'username', 'password']
            
            for field in required_fields:
                if field not in config or not config[field]:
                    self.logger.error(f"Missing required SMTP field: {field}")
                    return False
            
            # Validate port
            port = config['smtp_port']
            if not isinstance(port, int) or port <= 0 or port > 65535:
                self.logger.error(f"Invalid SMTP port: {port}")
                return False
            
            # Validate recipients
            recipients = config.get('recipients', [])
            if not isinstance(recipients, list) or not recipients:
                self.logger.error("Recipients must be a non-empty list")
                return False
            
            # Basic email validation for recipients
            for recipient in recipients:
                if not isinstance(recipient, str) or '@' not in recipient:
                    self.logger.error(f"Invalid email address: {recipient}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP configuration validation failed: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection without sending email.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.enabled:
                self.logger.info("Email notifications disabled")
                return True
            
            smtp_host = self.smtp_config['smtp_host']
            smtp_port = self.smtp_config['smtp_port']
            username = self.smtp_config['username']
            password = self.smtp_config['password']
            use_tls = self.smtp_config.get('use_tls', True)
            
            # Test connection
            server = smtplib.SMTP(smtp_host, smtp_port)
            
            if use_tls:
                server.starttls()
            
            server.login(username, password)
            server.quit()
            
            self.logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """
        Send a test email to verify configuration.
        
        Returns:
            True if test email sent successfully, False otherwise
        """
        try:
            if not self.enabled:
                self.logger.info("Email notifications disabled, cannot send test email")
                return False
            
            subject = "🧪 Trading Bot Email Test"
            body = f"""
🧪 EMAIL CONFIGURATION TEST

This is a test email from the Enhanced NIFTY Trading Bot.

📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ SMTP Configuration: Working
📧 Email Service: Active

If you received this email, your email notification setup is working correctly!

📧 Generated by Enhanced NIFTY Trading Bot
"""
            
            return self._send_email(subject, body)
            
        except Exception as e:
            self.logger.error(f"Test email failed: {e}")
            return False