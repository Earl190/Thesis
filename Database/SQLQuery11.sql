USE ChurchAttendanceDB;
GO

CREATE TABLE dbo.Demographics (
    DemographicID INT IDENTITY(1,1) PRIMARY KEY,
    LocationName NVARCHAR(255) NOT NULL UNIQUE,
    HouseholdPopulation INT DEFAULT 0,
    ApostolicCatholic INT DEFAULT 0,
    CatholicCharismatic INT DEFAULT 0,
    PhilippineIndependent INT DEFAULT 0,
    RomanCatholic INT DEFAULT 0,
    LastUpdated DATETIME2 DEFAULT SYSDATETIME()
);
GO

CREATE TABLE dbo.Demographics_Staging (
    location_name NVARCHAR(255),
    household_population INT,
    apostolic_catholic INT,
    catholic_charismatic INT,
    philippine_independent INT,
    roman_catholic INT
);
GO