app('address_width 22', echo=True)
app('line_size_width 9', echo=True)
app('create Apartado A', echo=True)
app('name Memory', echo=True)
app('memory', echo=True)
app('name Cache', echo=True)
app('set_width 2', echo=True)
app('way_width 0', echo=True)
app('policy LRU', echo=True)
app('write_back True', echo=True)
app('write_allocate True', echo=True)
app('cache', echo=True)
dir_a = 0x200000
dir_b = 0x200000 + 1024*4
dir_c = 0x200000 + 1024*4*2

for i in range(1024):
    app('read ' + str(dir_a + i*12+8), echo=False)
    app('read ' + str(dir_b + 12*(1023-i)*4+0), echo=False)
    app('write ' + str(dir_c + i*12+4), echo=False)

app('show_state stats', echo=True)

