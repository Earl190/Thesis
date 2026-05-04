CREATE INDEX IX_Events_EventDate ON dbo.Events(EventDate);
CREATE INDEX IX_FootTrafficRecords_EventID ON dbo.FootTrafficRecords(EventID);
CREATE INDEX IX_FootTrafficRecords_RecordDateTime ON dbo.FootTrafficRecords(RecordDateTime);
CREATE INDEX IX_ExternalFactors_EventID ON dbo.ExternalFactors(EventID);
CREATE INDEX IX_Predictions_EventID ON dbo.Predictions(EventID);
CREATE INDEX IX_SystemLogs_UserID ON dbo.SystemLogs(UserID);
GO
