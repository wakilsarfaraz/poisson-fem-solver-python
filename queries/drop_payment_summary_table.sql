 IF OBJECT_ID('payment_summary_table', 'U') IS NOT NULL
        BEGIN
            DROP TABLE payment_summary_table;
        END;