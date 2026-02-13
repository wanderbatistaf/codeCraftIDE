database stores_demo

globals
    define
        gv_customer_name varchar(30),
        gv_count integer
end globals

main
    define
        v_fname varchar(15),
        v_lname varchar(15)
    
    select fname, lname
      into v_fname, v_lname
      from customer
     where customer_num = 1
    
    display "Customer:", v_fname, v_lname
end main
