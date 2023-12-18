app('address_width 32', echo=True)
app('line_size_width 4', echo=True)
app('create Apartado A', echo=True)
app('name Memory', echo=True)
app('memory', echo=True)
app('name Cache', echo=True)
app('set_width 8', echo=True)
app('way_width 0', echo=True)
app('policy LRU', echo=True)
app('write_back True', echo=True)
app('write_allocate True', echo=True)
app('cache', echo=True)

dir_a = 0x200000
dir_b = 0x200000 + 1024*4 + 16
dir_c = 0x200000 + 1024*4*2 + 16

for i in range(10):
    for j in range(1024):
        app('read ' + str(dir_a + j*4), echo=False)
        app('read ' + str(dir_b + j*4), echo=False)
        app('write ' + str(dir_c + i*4), echo=False)

app('show_state stats', echo=True)