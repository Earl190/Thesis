import pandas as pd
import pyodbc
import datetime
from sqlalchemy import text
import numpy as np
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

def get_connection_string():
    server = r"EARL\SQLEXPRESS"   
    database = "ChurchAttendanceDB"

    connection_string = (
        "mssql+pyodbc:///?odbc_connect=" +
        quote_plus(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
        )
    )
    return connection_string

def get_engine():
    return create_engine(get_connection_string())

def load_attendance_data():
    query = """
        SELECT
            f.RecordID,
            CAST(e.EventDate AS date) AS [date],
            CONVERT(varchar(5), e.MassTime, 108) AS mass_time,
            f.AttendanceCount AS attendance,
            f.FootTrafficCount AS foot_traffic_count,
            f.Capacity AS capacity,
            e.EventType AS event_type,
            ISNULL(ef.HolidayFlag, 0) AS holiday_flag,
            ISNULL(ef.WeatherCondition, 'Unknown') AS weather_condition
        FROM dbo.FootTrafficRecords f
        INNER JOIN dbo.Events e
            ON f.EventID = e.EventID
        LEFT JOIN dbo.ExternalFactors ef
            ON e.EventID = ef.EventID
           AND ef.FactorDate = e.EventDate
        ORDER BY e.EventDate ASC, e.MassTime ASC
    """

    engine = get_engine()
    df = pd.read_sql(query, engine)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "date", "mass_time", "attendance", "foot_traffic_count",
                "capacity", "event_type", "holiday_flag", "weather_condition", "year"
            ]
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["mass_time"] = df["mass_time"].fillna("08:00")
    df["attendance"] = pd.to_numeric(df["attendance"], errors="coerce").fillna(0)
    df["foot_traffic_count"] = pd.to_numeric(df["foot_traffic_count"], errors="coerce").fillna(0)
    df["capacity"] = pd.to_numeric(df["capacity"], errors="coerce").fillna(500)
    df["holiday_flag"] = pd.to_numeric(df["holiday_flag"], errors="coerce").fillna(0)
    df["weather_condition"] = df["weather_condition"].fillna("Unknown")
    df["event_type"] = df["event_type"].fillna("Regular Mass")

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6]).astype(int)

    return df

def upload_demographic_data(df):
    engine = get_engine()
    try:
        df.columns = df.columns.str.strip()
        
        column_mapping = {
            'Region, Province, and Highly Urbanized City': 'location_name',
            'Household Population': 'household_population',
            'Apostolic Catholic Church, Inc.': 'apostolic_catholic',
            'Catholic Charismatic': 'catholic_charismatic',
            'Philippine Independent Catholic Church': 'philippine_independent',
            'Roman Catholic, excluding Catholic Charismatics': 'roman_catholic'
        }
        df = df.rename(columns=column_mapping)
        
        expected_columns = list(column_mapping.values())
        
        for col in expected_columns:
            if col not in df.columns:
                df[col] = 0
                
        df_filtered = df[expected_columns].copy()
        
        # 3. Drop empty rows
        df_filtered = df_filtered.dropna(subset=["location_name"])
        
        if df_filtered.empty:
            return False, "Upload failed: No valid locations found."

        df_filtered.to_sql("Demographics_Staging", con=engine, schema="dbo", if_exists="append", index=False)

        process_query = text("""
            -- Insert new locations
            INSERT INTO dbo.Demographics (LocationName, HouseholdPopulation, ApostolicCatholic, CatholicCharismatic, PhilippineIndependent, RomanCatholic)
            SELECT 
                location_name, MAX(household_population), MAX(apostolic_catholic), 
                MAX(catholic_charismatic), MAX(philippine_independent), MAX(roman_catholic)
            FROM dbo.Demographics_Staging
            WHERE NOT EXISTS (
                SELECT 1 FROM dbo.Demographics d WHERE d.LocationName = dbo.Demographics_Staging.location_name
            )
            GROUP BY location_name;

            -- Update existing locations if the data changed
            UPDATE d
            SET 
                d.HouseholdPopulation = s.household_population,
                d.RomanCatholic = s.roman_catholic,
                d.LastUpdated = SYSDATETIME()
            FROM dbo.Demographics d
            INNER JOIN dbo.Demographics_Staging s ON d.LocationName = s.location_name;

            -- Clean the staging table
            TRUNCATE TABLE dbo.Demographics_Staging;
        """)

        with engine.begin() as conn:
            conn.execute(process_query)

        return True, "Demographic data successfully uploaded and mapped!"
        
    except Exception as e:
        try:
            with engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE dbo.Demographics_Staging;"))
        except:
            pass
        return False, f"Upload Failed: {str(e)}"

def get_user_by_username(username):
    engine = get_engine()
    query = text("""
        SELECT TOP 1
            u.UserID,
            u.FullName,
            u.Email,
            u.Username,
            u.PasswordHash,
            r.RoleName AS Role 
        FROM dbo.Users u
        INNER JOIN dbo.Roles r
            ON u.RoleID = r.RoleID
        WHERE u.Username = :username
          AND u.IsActive = 1
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"username": username}).mappings().first()
        return dict(result) if result else None

def create_user(full_name, email, username, password, security_question, security_answer):
    engine = get_engine()

    check_query = text("""
        SELECT COUNT(*) AS total
        FROM dbo.Users
        WHERE Username = :username OR Email = :email
    """)

    insert_query = text("""
        INSERT INTO dbo.Users (
            FullName,
            Email,
            Username,
            PasswordHash,
            RoleID,
            IsActive,
            CreatedAt,
            SecurityQuestion,
            SecurityAnswer
        )
        VALUES (
            :full_name,
            :email,
            :username,
            :password,
            (SELECT TOP 1 RoleID FROM dbo.Roles WHERE RoleName = 'Staff'), -- ALREADY PERFECT: Defaulting to Staff dynamically
            1,
            SYSDATETIME(),
            :security_question,
            :security_answer
        )
    """)

    with engine.begin() as conn:
        existing = conn.execute(
            check_query,
            {"username": username, "email": email}
        ).scalar()

        if existing and existing > 0:
            return False, "Username or email already exists."

        conn.execute(
            insert_query,
            {
                "full_name": full_name,
                "email": email,
                "username": username,
                "password": password,
                "security_question": security_question,
                "security_answer": security_answer
            }
        )

    return True, "Account created successfully."

def get_user_by_email(email):
    engine = get_engine()
    query = text("""
        SELECT TOP 1
            UserID, FullName, Email, Username, SecurityQuestion, SecurityAnswer     
        FROM dbo.Users
        WHERE Email = :email
          AND IsActive = 1
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"email": email}).mappings().first()
        return dict(result) if result else None

def update_password_by_email(email, new_password):
    engine = get_engine()
    update_query = text("""
        UPDATE dbo.Users
        SET PasswordHash = :new_password
        WHERE Email = :email
    """)

    try:
        with engine.begin() as conn:
            conn.execute(update_query, {
                "new_password": new_password,
                "email": email
            })
        return True
    except Exception as e:
        return False

def upload_csv_data(df):
    """Uploads Pandas DataFrame to a staging table and processes it into the main normalized tables."""
    engine = get_engine()
    try:
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        expected_columns = [
            "date", "mass_time", "attendance", "foot_traffic_count",
            "capacity", "event_type", "holiday_flag", "weather_condition"
        ]
        
        for col in expected_columns:
            if col not in df.columns:
                df[col] = np.nan
                
        df_filtered = df[expected_columns].copy()
        
        df_filtered = df_filtered.dropna(subset=["date"])
        
        if df_filtered.empty:
            return False, "Upload failed: The CSV contains no valid dates."

        df_filtered.to_sql("Attendance_Staging", con=engine, schema="dbo", if_exists="append", index=False)

        step1_events = text("""
            INSERT INTO dbo.Events (EventDate, MassTime, EventType)
            SELECT 
                CAST([date] AS DATE), 
                CAST([mass_time] AS TIME), 
                MAX(ISNULL([event_type], 'Regular Mass'))
            FROM dbo.Attendance_Staging
            WHERE NOT EXISTS (
                SELECT 1 FROM dbo.Events e 
                WHERE e.EventDate = CAST(dbo.Attendance_Staging.[date] AS DATE)
                  AND e.MassTime = CAST(dbo.Attendance_Staging.[mass_time] AS TIME)
            )
            GROUP BY CAST([date] AS DATE), CAST([mass_time] AS TIME);
        """)

        step2_attendance = text("""
            INSERT INTO dbo.FootTrafficRecords (EventID, AttendanceCount, FootTrafficCount, Capacity)
            SELECT 
                e.EventID,
                SUM(CAST(ISNULL(s.attendance, 0) AS INT)),
                SUM(CAST(ISNULL(s.foot_traffic_count, 0) AS INT)),
                MAX(CAST(ISNULL(s.capacity, 500) AS INT))
            FROM dbo.Attendance_Staging s
            INNER JOIN dbo.Events e 
                ON CAST(s.[date] AS DATE) = e.EventDate 
                AND CAST(s.[mass_time] AS TIME) = e.MassTime
            GROUP BY e.EventID;
        """)

        step3_factors = text("""
            INSERT INTO dbo.ExternalFactors (EventID, FactorDate, HolidayFlag, WeatherCondition)
            SELECT 
                e.EventID,
                CAST(MAX(s.[date]) AS DATE),
                MAX(CAST(ISNULL(s.holiday_flag, 0) AS INT)),
                MAX(ISNULL(s.weather_condition, 'Unknown'))
            FROM dbo.Attendance_Staging s
            INNER JOIN dbo.Events e 
                ON CAST(s.[date] AS DATE) = e.EventDate 
                AND CAST(s.[mass_time] AS TIME) = e.MassTime
            WHERE NOT EXISTS (
                SELECT 1 FROM dbo.ExternalFactors ef WHERE ef.EventID = e.EventID
            )
            GROUP BY e.EventID;
        """)

        step4_cleanup = text("TRUNCATE TABLE dbo.Attendance_Staging;")

        with engine.begin() as conn:
            conn.execute(step1_events)
            conn.execute(step2_attendance)
            conn.execute(step3_factors)
            conn.execute(step4_cleanup)

        return True, "Data successfully uploaded and securely processed into all tables!"
        
    except Exception as e:
        try:
            with engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE dbo.Attendance_Staging;"))
        except:
            pass
        return False, f"Upload Failed: {str(e)}"
        
def backup_database():
    server = r"EARL\SQLEXPRESS" 
    database = "ChurchAttendanceDB"
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"C:\\DB_Backups\\ChurchAttendance_{timestamp}.bak"
    
    sql_command = f"BACKUP DATABASE [{database}] TO DISK = '{backup_file}'"

    try:
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(sql_command)
        cursor.close()
        conn.close()
        
        return True, backup_file
    except Exception as e:
        return False, str(e)