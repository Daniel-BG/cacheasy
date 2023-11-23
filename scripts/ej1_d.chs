address_width 32
line_size_width 8
create Apartado D
name Memory
memory
name Cache
set_width 5
way_width 2
policy LRU
write_back True
write_allocate True
cache
read 0x0C000000
read 0x0C010000
write 0x0C020000 
read 0x0C000004
read 0x0C010004
write 0x0C020004 
show_state stats