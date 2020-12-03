-- Cari açılış update
-- USE sde;

CREATE TRIGGER TRG_KHT_ICMAL ON ISD_NEW.dbo.KHT
INSTEAD OF INSERT
    AS
    -- GlobalID, KullanimHakTipi
--     IF UPDATE(KHT_TIP)
--         update ISD_NEW.dbo.KHT_ICMAL SET KHT_TIP = KHT_TIP WHERE KHT_GUID = GlobalID;

    INSERT INTO ISD_NEW.dbo.KHT_ICMAL (KHT_GUID, KHT_TIP)
    SELECT GlobalID, KullanimHakTipi FROM inserted;
go


USE [ISD_NEW]
GO
/****** Object:  Trigger [dbo].[v42_insert]    Script Date: 03-Dec-20 12:54:58 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER TRIGGER [dbo].[v42_insert] ON [dbo].[KHT_evw] INSTEAD OF INSERT AS
BEGIN
DECLARE @rowcount INTEGER
SET @rowcount = @@rowcount
IF @rowcount = 0 RETURN
-- Check if we are already in an edit session.
DECLARE @g_state_id BIGINT
DECLARE @g_protected CHAR(1)
DECLARE @g_is_default CHAR(1)
DECLARE @g_version_id INTEGER
DECLARE @state_is_set INTEGER
EXECUTE dbo.SDE_get_globals @g_state_id OUTPUT,@g_protected OUTPUT,@g_is_default OUTPUT,@g_version_id OUTPUT,@state_is_set OUTPUT
IF (@g_version_id = -1) AND (@g_is_default = '0')
BEGIN
  RAISERROR ('User must call edit_version before editing the view.',16,-1)
  RETURN
END

IF (@g_version_id = -1) AND (@g_is_default = '1') AND (@state_is_set = 1)
BEGIN
  RAISERROR ('Cannot call set_current_version before editing default version. Call set_default before editing.',16,-1)
  RETURN
END

DECLARE @ret INTEGER
DECLARE @current_state BIGINT
IF @g_version_id != -1  -- standard editing
BEGIN
  EXECUTE @ret = dbo.SDE_current_version_writable @current_state OUTPUT
  IF @ret <> 0 RETURN
END
ELSE -- default version editing
  SET @current_state = @g_state_id
DECLARE @next_row_id INTEGER
DECLARE @num_ids INTEGER
DECLARE @return_row_id INTEGER
DECLARE @num_return_ids INTEGER
DECLARE @archive_oid INTEGER
IF @rowcount = 1
BEGIN
  SELECT @next_row_id = OBJECTID FROM inserted
    IF (@next_row_id IS NULL)
    BEGIN
    EXECUTE DBO.i42_get_ids 2, 1, @next_row_id OUTPUT, @num_ids OUTPUT
    IF @num_ids > 1
    BEGIN
      SET @return_row_id = @next_row_id + 1
      SET @num_return_ids = @num_ids - 1
      EXECUTE DBO.i42_return_ids 2, @return_row_id, @num_return_ids
    END
  END

  -- If editing state 0, then the insert being performed
  -- must be written to the base table, not the adds table

  IF @current_state = 0
  BEGIN
  INSERT INTO DBO.KHT
  (OBJECTID,GlobalID,AdaNo,Parsel,Eski_Kira_ID,Eski_Kira_No,aciklama,Eski_Parsel_ID,Durum,KullanimHakTipi,created_user,created_date,last_edited_user,last_edited_date)
  SELECT
  @next_row_id,i.GlobalID,i.AdaNo,i.Parsel,i.Eski_Kira_ID,i.Eski_Kira_No,i.aciklama,i.Eski_Parsel_ID,i.Durum,i.KullanimHakTipi,i.created_user,i.created_date,i.last_edited_user,i.last_edited_date  FROM inserted i
  END
  ELSE
  BEGIN
  INSERT INTO DBO.a42
  (OBJECTID,GlobalID,AdaNo,Parsel,Eski_Kira_ID,Eski_Kira_No,aciklama,Eski_Parsel_ID,Durum,KullanimHakTipi,created_user,created_date,last_edited_user,last_edited_date,SDE_STATE_ID)
  SELECT
  @next_row_id,i.GlobalID,i.AdaNo,i.Parsel,i.Eski_Kira_ID,i.Eski_Kira_No,i.aciklama,i.Eski_Parsel_ID,i.Durum,i.KullanimHakTipi,i.created_user,i.created_date,i.last_edited_user,i.last_edited_date,@current_state  FROM inserted i
  END
END
ELSE
BEGIN
  --Multi-row insert, need to cursor through the changes.
  DECLARE ins_cursor CURSOR FOR
  SELECT OBJECTID,GlobalID,AdaNo,Parsel,Eski_Kira_ID,Eski_Kira_No,aciklama,Eski_Parsel_ID,Durum,KullanimHakTipi,created_user,created_date,last_edited_user,last_edited_date,SDE_STATE_ID
  FROM inserted
  DECLARE @col1 int
  DECLARE @col2 uniqueidentifier
  DECLARE @col3 smallint
  DECLARE @col4 nvarchar(50)
  DECLARE @col5 int
  DECLARE @col6 nvarchar(50)
  DECLARE @col7 nvarchar(max)
  DECLARE @col8 int
  DECLARE @col9 nvarchar(255)
  DECLARE @col10 nvarchar(255)
  DECLARE @col11 nvarchar(255)
  DECLARE @col12 datetime2
  DECLARE @col13 nvarchar(255)
  DECLARE @col14 datetime2
  DECLARE @col15 bigint
  OPEN ins_cursor
  FETCH NEXT FROM ins_cursor INTO @col1,@col2,@col3,@col4,@col5,@col6,@col7,@col8,@col9,@col10,@col11,@col12,@col13,@col14,@col15
  WHILE @@FETCH_STATUS = 0
  BEGIN
    EXECUTE DBO.i42_get_ids 2, 1, @next_row_id OUTPUT, @num_ids OUTPUT
    IF @num_ids > 1
    BEGIN
      SET @return_row_id = @next_row_id + 1
      SET @num_return_ids = @num_ids - 1
      EXECUTE DBO.i42_return_ids 2, @return_row_id, @num_return_ids
    END
    IF @current_state = 0
    BEGIN
      -- If editing state 0, then the insert being performed
      -- must be written to the base table, not the adds table

      INSERT INTO DBO.KHT
      (OBJECTID,GlobalID,AdaNo,Parsel,Eski_Kira_ID,Eski_Kira_No,aciklama,Eski_Parsel_ID,Durum,KullanimHakTipi,created_user,created_date,last_edited_user,last_edited_date)
      VALUES (@next_row_id,@col2,@col3,@col4,@col5,@col6,@col7,@col8,@col9,@col10,@col11,@col12,@col13,@col14 )
    END
    ELSE
    BEGIN
      INSERT INTO DBO.a42
      (OBJECTID,GlobalID,AdaNo,Parsel,Eski_Kira_ID,Eski_Kira_No,aciklama,Eski_Parsel_ID,Durum,KullanimHakTipi,created_user,created_date,last_edited_user,last_edited_date,SDE_STATE_ID)
      VALUES (@next_row_id,@col2,@col3,@col4,@col5,@col6,@col7,@col8,@col9,@col10,@col11,@col12,@col13,@col14,@current_state )
    END

    FETCH NEXT FROM ins_cursor INTO @col1,@col2,@col3,@col4,@col5,@col6,@col7,@col8,@col9,@col10,@col11,@col12,@col13,@col14,@col15
  END
  CLOSE ins_cursor
  DEALLOCATE ins_cursor
END
IF (SELECT COUNT (*) FROM dbo.SDE_mvtables_modified WHERE state_id = @current_state AND registration_id = 42) = 0
 AND @current_state > 0
EXECUTE dbo.SDE_mvmodified_table_insert 42, @current_state
END