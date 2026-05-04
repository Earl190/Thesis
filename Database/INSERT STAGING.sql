TRUNCATE TABLE dbo.StagingAttendance;
GO

BULK INSERT dbo.StagingAttendance
FROM 'C:\Users\earls\Downloads\Thesis\church_attendance_2020.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK,
    CODEPAGE = '65001'
);
GO

BULK INSERT dbo.StagingAttendance
FROM 'C:\Users\earls\Downloads\Thesis\church_attendance_2021.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK,
    CODEPAGE = '65001'
);
GO

BULK INSERT dbo.StagingAttendance
FROM 'C:\Users\earls\Downloads\Thesis\church_attendance_2022.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK,
    CODEPAGE = '65001'
);
GO

BULK INSERT dbo.StagingAttendance
FROM 'C:\Users\earls\Downloads\Thesis\church_attendance_2023.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK,
    CODEPAGE = '65001'
);
GO

BULK INSERT dbo.StagingAttendance
FROM 'C:\Users\earls\Downloads\Thesis\church_attendance_2024.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK,
    CODEPAGE = '65001'
);
GO

BULK INSERT dbo.StagingAttendance
FROM 'C:\Users\earls\Downloads\Thesis\church_attendance_2025.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK,
    CODEPAGE = '65001'
);
GO