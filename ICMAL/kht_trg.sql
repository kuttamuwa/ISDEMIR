-- Cari açılış update
-- USE sde;

CREATE TRIGGER TRG_KHT_ICMAL
    ON ISD_NEW.dbo.KHT_TEST
    INSTEAD OF INSERT
    AS
    -- GlobalID, KullanimHakTipi
--     IF UPDATE(KHT_TIP)
--         update ISD_NEW.dbo.KHT_ICMAL SET KHT_TIP = KHT_TIP WHERE KHT_GUID = GlobalID;
    DECLARE
        @myval int
EXEC dbo.next_rowid 'dbo', 'KHT_ICMAL', @myval OUTPUT
SELECT @myval "Next RowID";
INSERT INTO ISD_NEW.dbo.KHT_ICMAL (KHT_GUID, KHT_TIP, OBJECTID)
SELECT GlobalID, KullanimHakTipi, @myval
FROM inserted;
go
