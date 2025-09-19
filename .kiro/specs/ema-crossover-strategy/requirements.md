# Requirements Document

## Introduction

This feature adds multiple advanced trading strategies to the existing stock trading bot: EMA (Exponential Moving Average) crossover strategy and SuperTrend strategy. The system will also include a multi-strategy scoring mechanism that combines signals from different strategies to provide weighted trading recommendations. The EMA crossover strategy detects when shorter-period EMAs approach or cross longer-period EMAs, while SuperTrend identifies trend direction and potential reversal points. Email notifications will be sent when significant signals occur.

## Requirements

### Requirement 1

**User Story:** As a trader, I want to receive signals when EMA crossovers occur, so that I can identify potential trend changes and trading opportunities.

#### Acceptance Criteria

1. WHEN a shorter EMA (e.g., 50-period) crosses above a longer EMA (e.g., 200-period) THEN the system SHALL generate a bullish crossover signal
2. WHEN a shorter EMA crosses below a longer EMA THEN the system SHALL generate a bearish crossover signal
3. WHEN EMAs are approaching within a configurable threshold distance THEN the system SHALL generate an approaching crossover signal
4. IF the crossover signal is generated THEN the system SHALL include the stock symbol, crossover type, current price, and EMA values in the signal data

### Requirement 2

**User Story:** As a trader, I want to configure different EMA periods for crossover detection, so that I can customize the strategy to my trading preferences.

#### Acceptance Criteria

1. WHEN configuring the EMA crossover strategy THEN the system SHALL allow setting custom short EMA period (default 50)
2. WHEN configuring the EMA crossover strategy THEN the system SHALL allow setting custom long EMA period (default 200)
3. WHEN configuring the approach threshold THEN the system SHALL allow setting the percentage distance for "approaching" signals (default 2%)
4. IF invalid EMA periods are provided (short >= long) THEN the system SHALL reject the configuration with an error message

### Requirement 3

**User Story:** As a trader, I want to receive email notifications when EMA crossover signals occur, so that I can be alerted immediately without constantly monitoring the system.

#### Acceptance Criteria

1. WHEN an EMA crossover signal is generated THEN the system SHALL send an email notification to configured recipients
2. WHEN sending email notifications THEN the system SHALL include signal type, stock symbol, current price, EMA values, and timestamp
3. WHEN email sending fails THEN the system SHALL log the error and continue processing without stopping the analysis
4. IF email configuration is missing or invalid THEN the system SHALL log a warning and skip email notifications

### Requirement 4

**User Story:** As a trader, I want the EMA crossover strategy to integrate with the existing trading bot framework, so that it works seamlessly with other indicators and strategies.

#### Acceptance Criteria

1. WHEN the EMA crossover strategy is enabled THEN the system SHALL calculate EMA values using the existing technical analysis framework
2. WHEN generating signals THEN the system SHALL follow the existing signal format and storage mechanisms
3. WHEN processing multiple stocks THEN the system SHALL apply the EMA crossover analysis to each symbol in the watchlist
4. IF insufficient historical data exists for EMA calculation THEN the system SHALL skip the symbol and log a warning

### Requirement 5

**User Story:** As a trader, I want to see EMA crossover signals in the output files and logs, so that I can review and analyze the signals later.

#### Acceptance Criteria

1. WHEN EMA crossover signals are generated THEN the system SHALL include them in the CSV output file
2. WHEN logging signal information THEN the system SHALL include EMA crossover details in the log messages
3. WHEN storing signals in the database THEN the system SHALL save EMA crossover signals with all relevant metadata
4. IF no EMA crossover signals are found THEN the system SHALL log this information for transparency

### Requirement 6

**User Story:** As a trader, I want to use SuperTrend indicator signals, so that I can identify trend direction and potential reversal points.

#### Acceptance Criteria

1. WHEN calculating SuperTrend indicator THEN the system SHALL use configurable ATR period (default 10) and multiplier (default 3.0)
2. WHEN price is above SuperTrend line THEN the system SHALL generate a bullish SuperTrend signal
3. WHEN price is below SuperTrend line THEN the system SHALL generate a bearish SuperTrend signal
4. WHEN SuperTrend changes from bearish to bullish THEN the system SHALL generate a trend reversal buy signal
5. WHEN SuperTrend changes from bullish to bearish THEN the system SHALL generate a trend reversal sell signal

### Requirement 7

**User Story:** As a trader, I want to combine multiple strategy signals with weighted scoring, so that I can get more reliable trading recommendations based on multiple indicators.

#### Acceptance Criteria

1. WHEN multiple strategies generate signals THEN the system SHALL calculate a composite score for each stock
2. WHEN configuring strategy weights THEN the system SHALL allow setting custom weights for EMA crossover, SuperTrend, and existing strategies
3. WHEN calculating composite scores THEN the system SHALL normalize individual strategy signals to a common scale (-100 to +100)
4. WHEN composite score exceeds configurable thresholds THEN the system SHALL generate strong buy/sell recommendations
5. IF strategy weights are not configured THEN the system SHALL use equal weighting for all enabled strategies

### Requirement 8

**User Story:** As a trader, I want to configure which strategies to enable and their relative importance, so that I can customize the trading system to my preferences.

#### Acceptance Criteria

1. WHEN configuring strategies THEN the system SHALL allow enabling/disabling individual strategies (EMA crossover, SuperTrend, existing RSI/Bollinger)
2. WHEN setting strategy weights THEN the system SHALL validate that weights are positive numbers
3. WHEN no strategies are enabled THEN the system SHALL display an error and refuse to run
4. IF strategy configuration is invalid THEN the system SHALL use default settings and log a warning

### Requirement 9

**User Story:** As a trader, I want to receive email notifications for high-confidence multi-strategy signals, so that I can focus on the most promising opportunities.

#### Acceptance Criteria

1. WHEN composite score exceeds strong buy threshold THEN the system SHALL send email notification with all contributing strategy details
2. WHEN composite score falls below strong sell threshold THEN the system SHALL send email notification with breakdown of signals
3. WHEN sending multi-strategy notifications THEN the system SHALL include individual strategy scores and composite score
4. IF email sending fails THEN the system SHALL log the error and continue processing without stopping

### Requirement 10

**User Story:** As a system administrator, I want to configure email settings for notifications, so that the system can send alerts to the appropriate recipients.

#### Acceptance Criteria

1. WHEN configuring email settings THEN the system SHALL support SMTP server configuration (host, port, security)
2. WHEN configuring email authentication THEN the system SHALL support username/password authentication
3. WHEN configuring recipients THEN the system SHALL support multiple email addresses for notifications
4. IF email configuration is provided THEN the system SHALL validate the settings during startup

### Requirement 11

**User Story:** As a trader, I want to see detailed multi-strategy analysis in outputs, so that I can understand how different indicators contribute to the final recommendations.

#### Acceptance Criteria

1. WHEN generating output files THEN the system SHALL include individual strategy scores and composite scores
2. WHEN logging analysis results THEN the system SHALL show breakdown of each strategy's contribution
3. WHEN storing in database THEN the system SHALL save individual strategy signals and composite scores
4. IF no strategies generate signals THEN the system SHALL log this information with strategy status details