-- Test DATETIME and INTERVAL qualifiers
MAIN
    -- Define variables with different datetime qualifiers
    DEFINE order_time DATETIME YEAR TO SECOND
    DEFINE order_date DATETIME YEAR TO DAY
    DEFINE ship_date DATETIME YEAR TO MONTH

    -- Define variables with interval qualifiers
    DEFINE time_elapsed INTERVAL HOUR TO MINUTE
    DEFINE duration INTERVAL DAY TO SECOND
    DEFINE age_years INTERVAL YEAR TO MONTH

    -- Test with actual datetime values
    LET order_time = CURRENT()
    LET order_date = TODAY()

    -- Display results
    DISPLAY "Order time: ", order_time
    DISPLAY "Order date: ", order_date

    -- Test datetime functions with qualifiers
    DEFINE event_date DATETIME YEAR TO DAY
    LET event_date = TODAY()

    DISPLAY "Event date (YEAR TO DAY): ", event_date
    DISPLAY "Year: ", YEAR(event_date)
    DISPLAY "Month: ", MONTH(event_date)
    DISPLAY "Day: ", DAY(event_date)

    -- Test simple datetime without qualifier
    DEFINE simple_date DATETIME
    LET simple_date = CURRENT()
    DISPLAY "Simple datetime: ", simple_date

END MAIN
