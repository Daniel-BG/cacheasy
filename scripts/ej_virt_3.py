app('virtual_address_width 24', echo=False)
app('address_width 15', echo=False)
app('line_size_width 12', echo=False)
app('create Ej virt 3', echo=False)
app('policy LRU', echo=False)
app('name Physical', echo=False)
app('set_width 3', echo=False)
app('way_width 0', echo=False)
app('cache', echo=False)
app('name Cache', echo=False)
app('line_size_width 6', echo=False)
app('set_width 6', echo=False)
app('way_width 1', echo=False)
app('cache', echo=False)
app('line_size_width 12', echo=False)
app('name Virtual', echo=False)
app('virtual', echo=False)

app('read 0x100000', echo=False)
app('read 0x101000', echo=False)
app('read 0x200000', echo=False)
app('read 0x201000', echo=False)
app('read 0x300000', echo=False)
app('read 0x301000', echo=False)
app('read 0x400000', echo=False)
app('read 0x401000', echo=False)

app('reset_stats', echo=False)


for i in range(16384):
    addr = 0x100000 + i*4
    app(f'read {addr}', echo=False)

app('show_state stats', echo=True)