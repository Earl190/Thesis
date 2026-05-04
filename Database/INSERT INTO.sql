INSERT INTO dbo.Roles (RoleName)
VALUES
('Admin'),
('Staff');
GO

INSERT INTO dbo.Users (
    FullName,
    Email,
    Username,
    PasswordHash,
    SecurityQuestion,
    SecurityAnswerHash,
    RoleID
)
VALUES
(
    'Administrator',
    'admin@church.local',
    'admin',
    'admin123',
    'What is your favorite saint?',
    'sample_answer_hash',
    1
),
(
    'Church Staff',
    'staff@church.local',
    'staff',
    'staff123',
    'What is your birth month?',
    'sample_answer_hash',
    2
);
GO

INSERT INTO dbo.Events (
    EventName,
    EventType,
    EventDate,
    MassTime,
    Description,
    CreatedByUserID
)
VALUES
('Morning Mass', 'Regular Mass', '2026-04-13', '08:00:00', 'Regular weekday mass', 1),
('Sunday Mass', 'Sunday Mass', '2026-04-19', '10:00:00', 'Main Sunday service', 1),
('Holy Week Celebration', 'Holiday Mass', '2026-04-17', '18:00:00', 'Special Holy Week event', 1);
GO

INSERT INTO dbo.FootTrafficRecords (
    EventID,
    RecordDateTime,
    AttendanceCount,
    FootTrafficCount,
    Capacity,
    EnteredByUserID,
    Notes
)
VALUES
(1, '2026-04-13 08:30:00', 120, 120, 500, 2, 'Normal attendance'),
(2, '2026-04-19 10:30:00', 260, 260, 500, 2, 'High Sunday attendance'),
(3, '2026-04-17 18:30:00', 310, 310, 500, 2, 'Holiday event attendance');
GO

INSERT INTO dbo.ExternalFactors (
    EventID,
    FactorDate,
    WeatherCondition,
    HolidayFlag,
    SpecialEventNotes
)
VALUES
(1, '2026-04-13', 'Sunny', 0, NULL),
(2, '2026-04-19', 'Cloudy', 0, 'Sunday service'),
(3, '2026-04-17', 'Rainy', 1, 'Holy Week');
GO

INSERT INTO dbo.Predictions (
    EventID,
    PredictionDate,
    PredictedAttendance,
    ConfidenceScore,
    ModelType,
    ModelMAE,
    Notes
)
VALUES
(1, SYSDATETIME(), 135, 88.50, 'Simple Linear Regression', 12.30, 'Prediction based on foot traffic'),
(2, SYSDATETIME(), 275, 91.20, 'Time Series Forecasting', 10.10, 'Forecast based on attendance trend');
GO

INSERT INTO dbo.SystemLogs (
    UserID,
    LogAction,
    IPAddress,
    Details
)
VALUES
(1, 'LOGIN', '127.0.0.1', 'Admin logged in'),
(2, 'ADD_ATTENDANCE', '127.0.0.1', 'Added attendance record for Sunday Mass'),
(1, 'RUN_PREDICTION', '127.0.0.1', 'Executed predictive model');
GO

INSERT INTO dbo.Feedback (
    EventID,
    SubmittedByUserID,
    Rating,
    Comment
)
VALUES
(2, 2, 5, 'Attendance report was accurate and useful.');
GO