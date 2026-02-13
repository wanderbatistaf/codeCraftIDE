-- Sample 4GL code demonstrating nested block structures
-- This showcases the enhanced block visualization features in Story 3.2

MAIN
  DEFINE counter INTEGER
  DEFINE name VARCHAR(50)
  DEFINE age INTEGER
  DEFINE i INTEGER

  -- Initialize variables
  LET counter = 0
  LET name = "John Doe"
  LET age = 30

  -- Simple IF block
  IF age > 18 THEN
    DISPLAY "Adult: ", name
    LET counter = counter + 1
  ELSE
    DISPLAY "Minor: ", name
  ENDIF

  -- Nested IF blocks
  IF age > 18 THEN
    IF age < 65 THEN
      DISPLAY "Working age adult"

      IF age < 30 THEN
        DISPLAY "Young professional"
      ELSE
        DISPLAY "Experienced professional"
      ENDIF
    ELSE
      DISPLAY "Retirement age"
    ENDIF
  ENDIF

  -- FOR loop with nested IF
  FOR i = 1 TO 5
    DISPLAY "Iteration: ", i

    IF i MOD 2 = 0 THEN
      DISPLAY "  Even number"
    ELSE
      DISPLAY "  Odd number"
    ENDIF
  ENDFOR

  -- WHILE loop with nested blocks
  LET counter = 0
  WHILE counter < 3
    LET counter = counter + 1
    DISPLAY "Counter: ", counter

    IF counter = 2 THEN
      DISPLAY "  Middle iteration"

      FOR i = 1 TO 2
        DISPLAY "    Nested loop: ", i
      ENDFOR
    ENDIF
  ENDWHILE

  -- CASE statement with nested blocks
  CASE
    WHEN age < 18
      DISPLAY "Age category: Minor"
      IF age < 13 THEN
        DISPLAY "  Subcategory: Child"
      ELSE
        DISPLAY "  Subcategory: Teenager"
      ENDIF

    WHEN age >= 18 AND age < 65
      DISPLAY "Age category: Adult"
      FOR i = 1 TO 3
        DISPLAY "  Processing adult record: ", i
      ENDFOR

    OTHERWISE
      DISPLAY "Age category: Senior"
      LET counter = 0
      WHILE counter < 2
        LET counter = counter + 1
        DISPLAY "  Senior benefits check: ", counter
      ENDWHILE
  ENDCASE

  DISPLAY "Program completed. Total checks: ", counter

END MAIN
