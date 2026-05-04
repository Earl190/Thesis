USE ChurchAttendanceDB;
GO

IF OBJECT_ID('dbo.StagingAttendance', 'U') IS NOT NULL
    DROP TABLE dbo.StagingAttendance;
GO

CREATE TABLE dbo.StagingAttendance (
    [date] NVARCHAR(50),
    mass_time NVARCHAR(20),
    attendance INT,
    foot_traffic_count INT,
    capacity INT,
    event_type NVARCHAR(50),
    weather_condition NVARCHAR(50),
    holiday_flag INT,
    special_event_notes NVARCHAR(255),
    day_of_week NVARCHAR(20),
    [month] INT,
    quarter NVARCHAR(10),
    attendance_rate FLOAT,
    low_attendance_alert INT
);
GO