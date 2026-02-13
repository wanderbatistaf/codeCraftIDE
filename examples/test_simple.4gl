database stores_demo

main
    define v_fname varchar(15)
    define v_lname varchar(15)
    
    select fname, lname into v_fname, v_lname from customer where customer_num = 1
    
    display "Customer:", v_fname, v_lname
end main
