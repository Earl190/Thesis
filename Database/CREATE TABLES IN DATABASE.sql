CREATE TABLE dbo.Roles (
    RoleID INT IDENTITY(1,1) PRIMARY KEY,
    RoleName NVARCHAR(50) NOT NULL UNIQUE
);
GO

CREATE TABLE dbo.Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    FullName NVARCHAR(100) NOT NULL,
    Email NVARCHAR(100) NOT NULL UNIQUE,
    Username NVARCHAR(50) NOT NULL UNIQUE,
    PasswordHash NVARCHAR(255) NOT NULL,
    SecurityQuestion NVARCHAR(255) NULL,
    SecurityAnswerHash NVARCHAR(255) NULL,
    RoleID INT NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_Users_Roles
        FOREIGN KEY (RoleID) REFERENCES dbo.Roles(RoleID)
);
GO

CREATE TABLE dbo.Events (
    EventID INT IDENTITY(1,1) PRIMARY KEY,
    EventName NVARCHAR(150) NOT NULL,
    EventType NVARCHAR(50) NOT NULL,
    EventDate DATE NOT NULL,
    MassTime TIME NULL,
    Description NVARCHAR(255) NULL,
    CreatedByUserID INT NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_Events_Users
        FOREIGN KEY (CreatedByUserID) REFERENCES dbo.Users(UserID),

    CONSTRAINT CHK_Events_EventType
        CHECK (EventType IN ('Regular Mass', 'Sunday Mass', 'Wedding', 'Funeral', 'Holiday Mass', 'Feast', 'Special Event'))
);
GO

CREATE TABLE dbo.FootTrafficRecords (
    RecordID INT IDENTITY(1,1) PRIMARY KEY,
    EventID INT NOT NULL,
    RecordDateTime DATETIME2 NOT NULL,
    AttendanceCount INT NOT NULL,
    FootTrafficCount INT NULL,
    Capacity INT NOT NULL DEFAULT 500,
    EnteredByUserID INT NOT NULL,
    Notes NVARCHAR(255) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_FootTrafficRecords_Events
        FOREIGN KEY (EventID) REFERENCES dbo.Events(EventID),

    CONSTRAINT FK_FootTrafficRecords_Users
        FOREIGN KEY (EnteredByUserID) REFERENCES dbo.Users(UserID),

    CONSTRAINT CHK_FootTrafficRecords_AttendanceCount
        CHECK (AttendanceCount >= 0),

    CONSTRAINT CHK_FootTrafficRecords_FootTrafficCount
        CHECK (FootTrafficCount IS NULL OR FootTrafficCount >= 0),

    CONSTRAINT CHK_FootTrafficRecords_Capacity
        CHECK (Capacity > 0)
);
GO

CREATE TABLE dbo.ExternalFactors (
    FactorID INT IDENTITY(1,1) PRIMARY KEY,
    EventID INT NOT NULL,
    FactorDate DATE NOT NULL,
    WeatherCondition NVARCHAR(50) NULL,
    HolidayFlag BIT NOT NULL DEFAULT 0,
    SpecialEventNotes NVARCHAR(255) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_ExternalFactors_Events
        FOREIGN KEY (EventID) REFERENCES dbo.Events(EventID),

    CONSTRAINT CHK_ExternalFactors_WeatherCondition
        CHECK (
            WeatherCondition IS NULL OR
            WeatherCondition IN ('Sunny', 'Cloudy', 'Rainy', 'Stormy', 'Unknown')
        )
);
GO

CREATE TABLE dbo.Predictions (
    PredictionID INT IDENTITY(1,1) PRIMARY KEY,
    EventID INT NOT NULL,
    PredictionDate DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    PredictedAttendance INT NOT NULL,
    ConfidenceScore DECIMAL(5,2) NULL,
    ModelType NVARCHAR(50) NOT NULL,
    ModelMAE DECIMAL(10,2) NULL,
    Notes NVARCHAR(255) NULL,

    CONSTRAINT FK_Predictions_Events
        FOREIGN KEY (EventID) REFERENCES dbo.Events(EventID),

    CONSTRAINT CHK_Predictions_PredictedAttendance
        CHECK (PredictedAttendance >= 0),

    CONSTRAINT CHK_Predictions_ConfidenceScore
        CHECK (ConfidenceScore IS NULL OR (ConfidenceScore >= 0 AND ConfidenceScore <= 100)),

    CONSTRAINT CHK_Predictions_ModelType
        CHECK (ModelType IN ('Simple Linear Regression', 'Time Series Forecasting'))
);
GO

CREATE TABLE dbo.SystemLogs (
    LogID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NOT NULL,
    LogAction NVARCHAR(100) NOT NULL,
    LogTimestamp DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    IPAddress NVARCHAR(45) NULL,
    Details NVARCHAR(255) NULL,

    CONSTRAINT FK_SystemLogs_Users
        FOREIGN KEY (UserID) REFERENCES dbo.Users(UserID),

    CONSTRAINT CHK_SystemLogs_LogAction
        CHECK (
            LogAction IN (
                'LOGIN',
                'LOGOUT',
                'CREATE_EVENT',
                'UPDATE_EVENT',
                'DELETE_EVENT',
                'ADD_ATTENDANCE',
                'UPDATE_ATTENDANCE',
                'GENERATE_REPORT',
                'RUN_PREDICTION'
            )
        )
);
GO

CREATE TABLE dbo.Feedback (
    FeedbackID INT IDENTITY(1,1) PRIMARY KEY,
    EventID INT NOT NULL,
    SubmittedByUserID INT NULL,
    Rating INT NOT NULL,
    Comment NVARCHAR(500) NULL,
    SubmittedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_Feedback_Events
        FOREIGN KEY (EventID) REFERENCES dbo.Events(EventID),

    CONSTRAINT FK_Feedback_Users
        FOREIGN KEY (SubmittedByUserID) REFERENCES dbo.Users(UserID),

    CONSTRAINT CHK_Feedback_Rating
        CHECK (Rating BETWEEN 1 AND 5)
);
GO
