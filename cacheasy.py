from enum import Enum
import numpy as np
import math

rng = np.random.default_rng()

ReplacementPolicy = Enum('ReplacementPolicy', ['FIFO', 'LRU', 'MRU', 'RANDOM'])

from colorama import Fore, Back, Style
def prettydir(addr, totalbits, setbits, bytebits, brackets=True, tagcol = Fore.RED, virtualbits = 0):
    if totalbits == 0:
        return ""
    #calculate the toal amount of bits
    blockbits = totalbits - setbits - bytebits
    #convert addr to binary string of (totalbits)
    binstring = f"{addr:0{totalbits}b}" 
    #separate bits
    blockstr = binstring[:blockbits]
    setstr = binstring[blockbits:blockbits+setbits]
    bytebits = binstring[blockbits+setbits:]
    
    app_str = " " * (virtualbits - totalbits) if virtualbits > totalbits else ""

    if brackets:
        return f"[{app_str}{tagcol}{blockstr}{Fore.GREEN}{setstr}{Fore.BLUE}{bytebits}{Style.RESET_ALL}]"
    else:
        return f"{app_str}{tagcol}{blockstr}{Fore.GREEN}{setstr}{Fore.BLUE}{bytebits}{Style.RESET_ALL}"
    
prettytick = f"{Fore.GREEN}✔{Style.RESET_ALL}"
prettyfail = f"{Fore.RED}✘{Style.RESET_ALL}"
prettyright = f"{Fore.YELLOW}→{Style.RESET_ALL}"
prettyleft = f"{Fore.YELLOW}←{Style.RESET_ALL}"
prettyup = f"{Fore.BLUE}↑{Style.RESET_ALL}"
prettyupyellow = f"{Fore.YELLOW}↑{Style.RESET_ALL}"
prettydown = f"{Fore.BLUE}↓{Style.RESET_ALL}"
prettydowndown = f"{Fore.BLUE}⯯{Style.RESET_ALL}"
prettyswap = f"{Fore.YELLOW}⇆{Style.RESET_ALL}"
prettytrash = f"{Fore.MAGENTA}🗑{Style.RESET_ALL}"


def bits_to_power(bits, unit):
    if bits < 10:
        return f"{2**bits}{unit}"
    if bits < 20:
        return f"{2**(bits-10)}K{unit}"
    if bits < 30:
        return f"{2**(bits-20)}M{unit}"
    if bits < 40:
        return f"{2**(bits-30)}G{unit}" 
    if bits < 50:
        return f"{2**(bits-40)}T{unit}" 
    if bits < 60:
        return f"{2**(bits-50)}P{unit}" 
    return f"{2**(bits-60)}E{unit}"


from collections import OrderedDict


class VirtualMemory:
    
    #page table
    #virtual page, physical page (marco), active, edad
    
    def __init__(self, name, virtual_address_width, address_width, page_width):
        #sanity checks
        if virtual_address_width < address_width or address_width < page_width:
            raise Exception("Wrong virtual memory parameters")
        
        self.name = name
        self.virtual_address_width = virtual_address_width
        self.address_width = address_width
        self.page_width = page_width
        self.number_of_pages = 2**(self.address_width-self.page_width)
        self.statistics = CacheStatistics()
        #Page table is an ordered dictionary of virtual_page, phys_page values
        #being in the dictionary means the page is actively translated
        #the position in the dictionary is the age of the page
        #(older pages first due to OrderedDict implementation)
        self.page_table = OrderedDict() 
        
    def add_memory_system(self, memory_system):
        self.memory_system = memory_system
        
    def evict_load_page(self, virtual_page):
        if virtual_page not in self.page_table:
            self.statistics.line_miss += 1
            print(f"{prettydir(virtual_page * 2**self.page_width, self.virtual_address_width, 0, self.page_width)} {prettyfail} Virtual page 0x{virtual_page:0x} not found")
            physical_page = None
            if len(self.page_table) == self.number_of_pages:
                #evict
                self.statistics.line_evict += 1
                entry = self.page_table.popitem(last = False)
                print(f"{prettydir(virtual_page * 2**self.page_width, self.virtual_address_width, 0, self.page_width)} {prettyfail} Page table full. Invalidating virtual page 0x{entry[0]:0x} @ physical 0x{entry[1]:0x}")
                physical_page = entry[1] #this page will be the new physical one
                initial_address = physical_page * 2**self.page_width
                final_address = physical_page * 2**self.page_width + 2**self.page_width - 1
                self.memory_system.clear(initial_address, final_address)
                self.memory_system.load(initial_address)
                print(f"{prettydir(virtual_page * 2**self.page_width, self.virtual_address_width, 0, self.page_width)} {prettyswap} Virtual page 0x{virtual_page:0x} replaces 0x{entry[0]:0x} on physical page 0x{physical_page:0x}")
            else:
                self.statistics.line_pull += 1
                physical_page = len(self.page_table)
                initial_address = physical_page * 2**self.page_width
                self.memory_system.load(initial_address)
                print(f"{prettydir(virtual_page * 2**self.page_width, self.virtual_address_width, 0, self.page_width)} {prettydown} Virtual page 0x{virtual_page:0x} loaded into 0x{physical_page:0x}")
            self.page_table[virtual_page] = physical_page
        else:
            self.statistics.line_hit += 1
            physical_page = self.page_table[virtual_page]
            self.page_table.move_to_end(virtual_page)
            print(f"{prettydir(virtual_page * 2**self.page_width, self.virtual_address_width, 0, self.page_width)} {prettytick} Virtual page 0x{virtual_page:0x} found at physical 0x{physical_page:0x}")
        
                
            
    def get_physical_address(self, virtual_address):
        virtual_page = virtual_address >> self.page_width
        physical_page = self.page_table[virtual_page]
        offset = virtual_address % (2**self.page_width)
        return (physical_page << self.page_width) + offset
    
    def get_virtual_page_number(self, virtual_address):
        return virtual_address >> self.page_width
            
    def _read_virtual(self, virtual_address):
        virtual_page = self.get_virtual_page_number(virtual_address)
        self.evict_load_page(virtual_page)
        self.memory_system.read(self.get_physical_address(virtual_address))
        
    def _write_virtual(self, virtual_address):
        virtual_page = self.get_virtual_page_number(virtual_address)
        self.evict_load_page(virtual_page)
        self.memory_system.write(self.get_physical_address(virtual_address))
        
    def read(self, init, end = None, step = None):
        if end is None:
            end = init
        if step is None:
            step = 1
        for i in range(init, end + 1, step):
            print(f"{prettydir(i, self.virtual_address_width, 0, 0, tagcol = Fore.LIGHTCYAN_EX, virtualbits=self.virtual_address_width)}{Fore.YELLOW} R Virtual Read Request{Style.RESET_ALL}")
            self._read_virtual(i)

    def write(self, init, end = None, step = None):
        if end is None:
            end = init
        if step is None:
            step = 1
        for i in range(init, end + 1, step):
            print(f"{prettydir(i, self.virtual_address_width, 0, 0, tagcol = Fore.LIGHTCYAN_EX, virtualbits=self.virtual_address_width)}{Fore.YELLOW} W Virtual Write Request{Style.RESET_ALL}")
            self._write_virtual(i)
            
    def reset_statistics(self):
        self.statistics.reset()
        self.memory_system.reset_statistics()

    def show_state(self, only_stats = False):
        hits = self.statistics.line_hit
        total = self.statistics.line_hit + self.statistics.line_miss
        
        hitrate = (hits / total) * 100  if total > 0 else 0
        
        print(f"{Fore.BLUE}{Back.GREEN}{self.name}{Style.RESET_ALL}")
        printstr = f"Translations: {Fore.GREEN}{hits}{Style.RESET_ALL} hits out of {Fore.YELLOW}{total}{Style.RESET_ALL} requests ({hitrate:.2f} hit rate). {prettydown}{self.statistics.line_pull} pages pulled and {prettyup}{self.statistics.line_evict} pages swapped"
        numzeros_virt = (self.virtual_address_width - self.page_width + 3) // 4
        numzeros_phys = (self.address_width - self.page_width + 3) // 4
        if not only_stats:
            printstr += f"\n{'-'*(numzeros_phys+numzeros_virt + 7)}\n"
            
            translations = []
            for entry in self.page_table.items():
                translations.append(f"{Fore.RED}0x{entry[0]:0{numzeros_virt}x} {prettyright} {Fore.GREEN}0x{entry[1]:0{numzeros_phys}x}{Style.RESET_ALL}")
                
            printstr += "\n".join(translations)
        
        print(printstr)        
        self.memory_system.show_state(only_stats)


class MemorySystem:

    def __init__(self, address_width, virtual_address_width=0):
        self.address_width = address_width
        self.levels = []
        self.last_level = None
        #for pretty printing
        self.virtual_address_width = virtual_address_width

    def add_main(self, line_size_width, name = "Main Memory"):
        if self.last_level is not None:
            raise Exception("Can't add main memory below a cache level")
        self.last_level = MainMemory(address_width = self.address_width, line_size_width = line_size_width, name = name, virtual_address_width=self.virtual_address_width)
        self.levels.append(self.last_level)

    def add_cache(self, name, set_width, way_width, line_size_width, replacement_policy, write_back, write_allocate, prefetch):
        #if self.last_level is None:
        #    raise Exception("Add main memory before caches")
        new_cache = Cache(name = name, set_width = set_width, way_width = way_width, line_size_width = line_size_width, replacement_policy = replacement_policy, write_back = write_back, write_allocate = write_allocate, parent = self.last_level, victim = None, address_width = self.address_width, prefetch = prefetch, virtual_address_width=self.virtual_address_width)
        self.last_level = new_cache
        self.levels.append(self.last_level)

    def add_victim(self, name, set_width, way_width, line_size_width, replacement_policy):
        if self.last_level is None or not hasattr(self.last_level, 'victim'):
            raise Exception("Can't add victim to an empty memory system or to main memory directly. Add a cache first")
        victim = Cache(name, set_width, way_width, line_size_width = line_size_width, replacement_policy = replacement_policy, address_width = self.address_width, virtual_address_width=self.virtual_address_width)
        self.last_level.victim = victim

    def read(self, init, end = None, step = None):
        if end is None:
            end = init
        if step is None:
            step = 1
        for i in range(init, end + 1, step):
            print(f"{prettydir(i, self.address_width, 0, 0, tagcol = Fore.YELLOW, virtualbits=self.virtual_address_width)}{Fore.YELLOW} R Read Request{Style.RESET_ALL}")
            self.last_level.read(i)

    def write(self, init, end = None, step = None):
        if end is None:
            end = init
        if step is None:
            step = 1
        for i in range(init, end + 1, step):
            print(f"{prettydir(i, self.address_width, 0, 0, tagcol = Fore.YELLOW, virtualbits=self.virtual_address_width)}{Fore.YELLOW} W Write Request{Style.RESET_ALL}")
            self.last_level.write(i)

    def reset_statistics(self):
        for level in self.levels:
            level.reset_statistics()

    def show_state(self, only_stats = False):
        for level in self.levels:
            print(f"{Fore.BLUE}{Back.GREEN}{level.name}{Style.RESET_ALL}")
            if not only_stats:
                print(level)
            level.show_statistics()
            
    def show_costs(self):
        for level in self.levels:
            print(f"{Fore.BLUE}{Back.GREEN}{level.name}{Style.RESET_ALL}")
            level.show_costs()
            
    #clear from bottom up
    def clear(self, initial_address, final_address):
        self.last_level.clear(initial_address, final_address)
        
    #load from top down
    def load(self, initial_address):
        self.levels[0].load(initial_address)




class CacheLine:

    def __init__(self, addr, tag, valid = True, dirty = False):
        self.dirty = dirty
        self.addr = addr
        self.tag = tag
        self.valid = valid
        
    def prettyprint(self, tag_width):
        return f"{Fore.BLACK if not self.valid else Fore.GREEN}V{Style.RESET_ALL}{Fore.BLACK if not self.dirty else Fore.YELLOW}D{Style.RESET_ALL} {prettydir(self.tag, tag_width, 0, 0, brackets = False)}"
    
        
class CacheStatistics:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.cost_hit = 0
        self.cost_miss = 200
        self.cost_through = 50
        self.cost_access = 1
        
        self.read_hit = 0
        self.read_miss = 0

        self.write_hit = 0
        self.write_miss = 0
        self.write_through = 0

        self.victim_swap = 0
        self.victim_push = 0
        self.victim_evict = 0

        self.line_evict = 0
        self.line_miss = 0
        self.line_hit = 0
        self.line_pull = 0
        self.line_prefetch = 0

    def get_statistics(self, show_wt = True, show_prefetch = True, show_victim = True):
        total_reads = self.read_hit + self.read_miss
        hitrate_read = float(self.read_hit) / float(total_reads) * 100.0 if total_reads > 0 else 0
        total_writes = self.write_hit + self.write_miss
        hitrate_write = float(self.write_hit) / float(total_writes) * 100.0 if total_writes > 0 else 0
        hit_width = math.ceil(math.log10(1+max(self.read_hit, self.write_hit, self.line_hit)))
        mis_width = math.ceil(math.log10(1+max(self.read_miss, self.write_miss, self.line_miss)))
        tot_width = math.ceil(math.log10(1+max(total_reads, total_writes)))
        
        wttext = f"[{Fore.LIGHTMAGENTA_EX}{self.write_through}{Style.RESET_ALL}{prettyup} written through]" if show_wt else ""
        pftext = f"({prettydowndown}{self.line_prefetch} prefetched) " if show_prefetch else ""
        vctext = f"\nVictim: {prettyswap}{self.victim_swap} swapped {prettyright}{self.victim_push} pushed to victim {prettyupyellow}{self.victim_evict} evicted from victim" if show_victim else ""
        return f'Reads:  {Fore.GREEN}{self.read_hit:{hit_width}d}{Style.RESET_ALL} hits and {Fore.RED}{self.read_miss:{mis_width}d}{Style.RESET_ALL} misses out of {Fore.YELLOW}{total_reads:{tot_width}d}{Style.RESET_ALL} requests ({hitrate_read:.2f} hit rate) \n'+\
            f'Writes: {Fore.GREEN}{self.write_hit:{hit_width}d}{Style.RESET_ALL} hits and {Fore.RED}{self.write_miss:{mis_width}d}{Style.RESET_ALL} misses out of {Fore.YELLOW}{total_writes:{tot_width}d}{Style.RESET_ALL} requests ({hitrate_write:.2f} hit rate) {wttext}\n' + \
            f"Blocks: {Fore.GREEN}{self.line_hit:{hit_width}d}{Style.RESET_ALL} hits and {Fore.RED}{self.line_miss:{mis_width}d}{Style.RESET_ALL} misses. {prettydown}{self.line_pull} fetched {pftext}{prettyup}{self.line_evict} written back" + \
            vctext
            
    def get_cost(self, show_through=False):
        total_hit = self.read_hit + self.write_hit
        cost_hit = total_hit * self.cost_hit
        total_miss = self.read_miss + self.write_miss
        cost_miss = total_miss * self.cost_miss
        total_access = total_hit + total_miss
        cost_access = total_access * self.cost_access
        total_through = self.write_through
        cost_through = total_through * self.cost_through
        total_cost = cost_access + cost_hit + cost_miss + cost_through
        wttext = f". {Fore.BLUE}{total_through}{Style.RESET_ALL} write-through cost [{Fore.YELLOW}{cost_through}{Style.RESET_ALL}]" if show_through else ""
        return f'Cost: [{Fore.YELLOW}{total_cost}{Style.RESET_ALL}] total cost, of which: {Fore.YELLOW}{total_access}{Style.RESET_ALL} accesses cost [{Fore.YELLOW}{cost_access}{Style.RESET_ALL}], {Fore.GREEN}{total_hit}{Style.RESET_ALL} hits cost [{Fore.YELLOW}{cost_hit}{Style.RESET_ALL}], and {Fore.RED}{total_miss}{Style.RESET_ALL} misses cost [{Fore.YELLOW}{cost_miss}{Style.RESET_ALL}]{wttext}'


class MainMemory:

    def __init__(self, address_width, line_size_width, name = "Main memory", virtual_address_width = 0):
        self.name = name
        self.address_width = address_width
        self.line_size_width = line_size_width
        self.statistics = CacheStatistics()
        #for pretty printing
        self.virtual_address_width = virtual_address_width
        
    def __contains__(self, key):
        return key < (1 << self.address_width)

    def get_block(self, addr):
        return addr >> self.line_size_width

    def read(self, addr):
        self.statistics.read_hit += 1
        print(f"{prettydir(addr, self.address_width, 0, self.line_size_width, virtualbits=self.virtual_address_width)} {prettydown} Block 0x{self.get_block(addr):0x} read from main memory")
        return True

    def write(self, addr):
        self.statistics.write_hit += 1
        print(f"{prettydir(addr, self.address_width, 0, self.line_size_width, virtualbits=self.virtual_address_width)} {prettyup} Block 0x{self.get_block(addr):0x} written to main memory")
        return True

    def write_line(self, line):
        return self.write(line.addr)

    def show_statistics(self):
        print(f"{self.statistics.get_statistics(show_prefetch=False, show_victim=False, show_wt=False)}")
        
    def show_costs(self):
        print(f"{self.statistics.get_cost(show_through=False)}")

    def reset_statistics(self):
        self.statistics.reset()
        
    def reset_costs(self, cost_hit, cost_miss, cost_through):
        self.statistics.cost_hit = cost_hit
        self.statistics.cost_miss = cost_miss
        self.statistics.cost_through = cost_through
        
    def __str__(self):
        return f"{self.name}: {bits_to_power(self.address_width, 'B')} ({bits_to_power(self.address_width-self.line_size_width, ' Blocks')} of {bits_to_power(self.line_size_width, 'B')})"


class Cache:

    def __init__(self, name, set_width, way_width, line_size_width, replacement_policy = ReplacementPolicy.LRU, write_back = True, write_allocate = True, parent = None, victim = None, address_width = 32, prefetch = None, virtual_address_width=0):
        self.replacement_policy = replacement_policy

        #Log base two of the number of sets, ways and bytes per line
        self.set_width = set_width              
        self.way_width = way_width              
        self.line_size_width = line_size_width  

        #write back policy (only write when evicted)
        #if disabled it is write-through (write always to cache and behind (avoid dirty)
        self.write_back = write_back        
        #write allocate policy. If enabled, blocks are brought to cache when writing
        #if not enabled, blocks are written to main memory
        self.write_allocate = write_allocate
        #prefetch, when a block fails to be located, bring the X ones as well
        self.prefetch = prefetch

        self.parent = parent  #memory where we load from / write to. Might be None (e.g:victim)
        self.victim = victim        #victim cache. Might be None (e.g:mainmemory)

        #for pretty printing and statistics
        self.address_width = address_width 
        self.virtual_address_width = virtual_address_width
        self.name = name
        self.statistics = CacheStatistics()

        #initialize set structure: list of lists
        self.set_data = []
        for i in range(2**self.set_width):
            set_info = []
            for i in range(2**self.way_width):
                set_info.append(CacheLine(0, 0, False, False))
            self.set_data.append(set_info)


    def get_set_idx(self, addr):
        block = addr >> self.line_size_width
        return block % (2**self.set_width)

    def get_set(self, addr):
        return self.set_data[self.get_set_idx(addr)]
    
    def get_tag(self, addr):
        block = addr >> self.line_size_width
        tag_num = block >> self.set_width
        return tag_num

    def __contains__(self, key):
        candidate_set = self.get_set(key)
        for line in candidate_set:
            if line.valid and line.tag == self.get_tag(key):
                return True
        return False
        

    def read(self, addr):
        if addr in self:
            self.statistics.read_hit += 1
        else:
            self.statistics.read_miss += 1
        self.get(addr)
        self._update(addr) #update LRU, etc

    def write(self, addr):
        #allocate space before updating
        if self.write_allocate:
            if addr in self:
                self.statistics.write_hit += 1
            else:
                self.statistics.write_miss += 1

            self.get(addr)
            self._update(addr, dirty=True) #update LRU, etc
        else: 
            #if the block is here, write it
            if addr in self:
                self.statistics.write_hit += 1
                self.get(addr)
                self._update(addr, dirty=True) #update LRU, etc
            #if not, write next level
            else:
                self.statistics.write_through += 1
                self.parent.write(addr)


    #gets an address for this cache. Internal statistics are updated, and data is brought if needed
    def get(self, addr, prefetched = 0):
        value = self._get(addr, prefetched)
        self._update(addr)
        return value
        
    def _get(self, addr, prefetched = 0):
        if addr in self: #Data found!
            print(f"{prettydir(addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettytick} Tag 0x{self.get_tag(addr):0x} in {self.name} set 0x{self.get_set_idx(addr):0x}")
            self.statistics.line_hit += 1
            return True
        else: #data not found
            self.statistics.line_miss += 1
            if self.victim:
                if addr in self.victim: #data found in victim
                    print(f"{prettydir(addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettytick} Addr 0x{addr:0x} in {self.victim.name}")
                    line_from_cache = self.allocate_for(addr)
                    line_from_victim = self.victim.extract(addr)
                    self.victim.write_line(line_from_cache)
                    self.write_line(line_from_victim)
                    print(f"{prettydir(line_from_cache.addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettyright} Tag 0x{self.get_tag(line_from_cache.addr):0x} from {self.name} to {self.victim.name}")
                    print(f"{prettydir(line_from_victim.addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettyleft} Tag 0x{self.get_tag(line_from_victim.addr):0x} from {self.victim.name} to {self.name}")
                    self.statistics.victim_swap += 1
                    return True
                else: #data not in victim
                    print(f"{prettydir(addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettyfail} Tag 0x{self.get_tag(addr):0x} not in {self.name}")
                    line_from_cache = self.allocate_for(addr)
                    if line_from_cache.valid: #needs to go to victim cache
                        line_from_victim = self.victim.allocate_for(line_from_cache.addr)
                        self.victim.write_line(line_from_cache)
                        self.statistics.victim_push += 1
                        if line_from_victim.valid and line_from_victim.dirty: #needs to go to upper level
                            print(f"{prettydir(line_from_victim.addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettyright} Tag 0x{self.get_tag(line_from_victim.addr):0x} from {self.victim.name} to {self.parent.name}")
                            self.parent.write_line(line_from_victim)
                            self.statistics.victim_evict += 1
                        print(f"{prettydir(line_from_cache.addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettyright} Tag 0x{self.get_tag(line_from_cache.addr):0x} from {self.name} to {self.victim.name}")

            else: #no victim cache
                print(f"{prettydir(addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettyfail} Tag 0x{self.get_tag(addr):0x} not in {self.name} set 0x{self.get_set_idx(addr):0x}")
                line_from_cache = self.allocate_for(addr)
                if line_from_cache.valid and line_from_cache.dirty:
                    self.statistics.line_evict += 1
                    self.parent.write_line(line_from_cache)
                    print(f"{prettydir(line_from_cache.addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettyright} Tag 0x{self.get_tag(line_from_cache.addr):0x} from {self.name} to {self.parent.name}")


            #ask higher level for data since we did not find it inside or in victim
            self.statistics.line_pull += 1
            self.parent.read(addr)
            if addr not in self.parent:
                print("An address was requested to a memory that does not have it nor does it have a higher order memory connected")
                return False
            print(f"{prettydir(addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettyleft} Tag 0x{self.get_tag(addr):0x} from {self.parent.name} to {self.name} set 0x{self.get_set_idx(addr):0x}")
            self._write(addr, dirty=False)

            if self.prefetch is not None:
                if prefetched >= self.prefetch:
                    return True
                else:
                    self.statistics.line_prefetch += 1
                    return self.get(addr + 2**self.line_size_width, prefetched + 1)
            else:
                return True        
        

    def write_line(self, line):
        self._write(line.addr, line.dirty)

    def _write(self, addr, dirty=True):
        if addr in self:
            candidate_set = self.get_set(addr)
            for line in candidate_set:
                if line.valid and line.tag == self.get_tag(addr):
                    line.dirty |= dirty
                    self._update(addr)
                    return
            
            raise Exception("Adding an existing element")
        

        candidate_set = self.get_set(addr)

        match self.replacement_policy:
            case ReplacementPolicy.RANDOM:
                placed = False
                for (i, elem) in enumerate(candidate_set):
                    if not elem.valid:
                        elem = CacheLine(addr, self.get_tag(addr), valid=True, dirty=dirty)
                        placed = True
                        break

                if not placed:
                    raise Exception("ERROR")
            case _:
                #chech that there is empty space
                placed = False
                for (i, line) in enumerate(candidate_set):
                    if not line.valid:
                        placed = True
                        candidate_set[0] = CacheLine(addr, self.get_tag(addr), valid=True, dirty=dirty)
                        break

                if not placed:
                    raise Exception("ERROR")

                #update policy
                self._update(addr)

    #set last=True so the updated address goes to the last position
    def _update(self, addr, dirty=False, last=False):
        candidate_set = self.get_set(addr)
        for (i, line) in enumerate(candidate_set):
            if line.tag == self.get_tag(addr):
                match self.replacement_policy:
                    case ReplacementPolicy.LRU | ReplacementPolicy.MRU:
                        elem = candidate_set.pop(i)
                        elem.dirty = dirty
                        if last:
                            candidate_set.append(elem)
                        else:
                            candidate_set.insert(0, elem)
                    case _:
                        pass
                        #doesnt matter for the rest
                return True
        return False
        
        
    def allocate_for(self, addr, force=False):
        #can return an invalid line!! be careful
        if addr in self and not force:
            raise Exception("Cannot allocate for already existing address")

        candidate_set = self.get_set(addr)
        
        outgoing = None
        match self.replacement_policy:
            case ReplacementPolicy.RANDOM:
                index = rng.randint(0, 2**self.way_width-1)
                outgoing = candidate_set[index]
                candidate_set[index] = CacheLine(0, 0, False, False)
            case ReplacementPolicy.FIFO | ReplacementPolicy.LRU:
                outgoing = candidate_set.pop()
                candidate_set.insert(0, CacheLine(0, 0, False, False))
            case ReplacementPolicy.MRU:
                outgoing = candidate_set.pop(0)
                candidate_set.push(CacheLine(0, 0, False, False))
            case _:
                raise Exception("Using an unsupported policy")

        return outgoing

    def extract(self, addr):
        candidate_set = self.get_set(addr)
        elem = None
        for (i, line) in enumerate(candidate_set):
            if line.tag == self.get_tag(addr):
                elem = candidate_set[i]
                candidate_set[i] = CacheLine(0, 0, False, False)
                self._update(0, last=True)
                break
        #Must return a CacheLine otherwise throw error
        if elem is None:
            raise Exception("Did not find line for extraction")
        
        return elem

    def __str__(self):
        setstr = []
        for (i, seti) in enumerate(self.set_data):
            linestr = []
            for line in seti:
                hex_fmt = '0' + str((self.address_width + 3) // 4) + 'x'
                base_addr = line.tag * (2**(self.line_size_width + self.set_width)) + i*2**self.line_size_width if line.valid else 0
                high_addr = base_addr + 2**(self.line_size_width) - 1 if line.valid else 0
                linestr.append(f"{line.prettyprint(self.address_width - self.line_size_width - self.set_width)}{prettydir(i << self.line_size_width, self.line_size_width + self.set_width, self.set_width, self.line_size_width, brackets=False)} [{Fore.YELLOW if line.valid else Fore.BLACK}0x{format(base_addr, hex_fmt)}-0x{format(high_addr, hex_fmt)}{Style.RESET_ALL}]")

            setstr.append("\n".join(linestr))
            
        printwidth = (11+self.address_width+2*((self.address_width + 3) // 4))
        #indent = (printwidth - len(self.name)) // 2
        #{' '*indent}{self.name}\n
        title = f"{'-'*printwidth}\n"
                        
        if self.victim:
            return title + "\n".join(setstr) + "\nVictim\n" + str(self.victim)
        else:
            return title + "\n".join(setstr)
        
    def clear(self, address_low, address_high):
        if self.victim is not None:
            raise Exception("Clear function not implemented for the case where a victim is present")
        
        #print(f"Clearing from {address_low} to {address_high}")
        
        #clear just the possible lines that contain these addresses
        for address in range(address_low, address_high, 2**self.line_size_width):
            if address in self:
                line =  self.extract(address)
                self.statistics.line_evict += 1
                if self.parent:
                    if line.dirty:
                        self.parent.write_line(line)
                        print(f"{prettydir(line.addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettyup} Tag 0x{self.get_tag(line.addr):0x} from {self.name} pushed to {self.parent.name}")
                    else:
                        print(f"{prettydir(line.addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettytrash} Tag 0x{self.get_tag(line.addr):0x} cleared from set 0x{self.get_set_idx(line.addr):0x} @ {self.name}")
                else:
                    print(f"{prettydir(line.addr, self.address_width, self.set_width, self.line_size_width, virtualbits=self.virtual_address_width)} {prettytrash} Tag 0x{self.get_tag(line.addr):0x} cleared from set 0x{self.get_set_idx(line.addr):0x} @ {self.name}")
                
        if self.parent:
            self.parent.clear(address_low, address_high)
                
        
        
    def load(self, address):
        if address in self:
            raise Exception("When loading we should not get here")
        self._write(address, dirty=False) #no questions asked above. When calling this function address should not be in this memory

    def show_statistics(self):
        print(f"{self.statistics.get_statistics(show_prefetch=self.prefetch, show_victim=self.victim is not None, show_wt=not self.write_allocate)}")
    
    def show_costs(self):
        print(f"{self.statistics.get_cost(show_through=not self.write_allocate)}")

    def reset_statistics(self):
        self.statistics.reset()
        
    def reset_costs(self, cost_hit, cost_miss, cost_through, cost_access):
        self.statistics.cost_hit = cost_hit
        self.statistics.cost_miss = cost_miss
        self.statistics.cost_through = cost_through
        self.statistics.cost_access = cost_access



import cmd2

class Cacheasy(cmd2.Cmd):
    """Command processor for the Cacheasy App"""

    def __init__(self):
        self.memsys = None
        self.address_width = 32
        self.virtual_address_width = 0
        self.line_size_width = 8
        self.memory_name = "MEM"
        self.set_width = 3
        self.way_width = 3
        self.replacement_policy = ReplacementPolicy.LRU
        self.write_back = True
        self.write_allocate = True
        self.prefetch = 0
        
        self.cost_hit = 0
        self.cost_miss = 200
        self.cost_through = 50
        self.cost_access = 1
        super().__init__()
        

        
    def parse_number(self, input_str):
        try:
            # Try to parse as a decimal number
            result = int(input_str, 10)
        except ValueError:
            try:
                # If parsing as a decimal fails, try parsing as a hexadecimal number
                result = int(input_str, 16)
            except ValueError:
                # If both attempts fail, the input is not a valid number
                raise ValueError("Invalid number format")
        return result
    
    def do_read(self, args):
        """read <address> [final_address] [word_size]
        Requests a read from memory. If final address 
        is specified, it reads the whole range (inclusive).
        If word_size is specified, the requests are performed
        only for multiples of that size"""
        if not args:
            print("An address must be specified")
        
        parsed_args = [self.parse_number(s) for s in args.split()]

        if len(parsed_args) == 1:
            self.memsys.read(parsed_args[0])
        elif len(parsed_args) == 2:
            self.memsys.read(parsed_args[0], parsed_args[1])
        elif len(parsed_args) == 3:
            self.memsys.read(parsed_args[0], parsed_args[1], parsed_args[2])
        else:
            print("Too many args")
            
    def do_write(self, args):
        """write <address> [final_address] [word_size]
        Requests a write to memory. If final address 
        is specified, it writes the whole range (inclusive).
        If word_size is specified, the requests are performed
        only for multiples of that size"""
        if not args:
            print("An address must be specified")
        
        parsed_args = [self.parse_number(s) for s in args.split()]

        if len(parsed_args) == 1:
            self.memsys.write(parsed_args[0])
        elif len(parsed_args) == 2:
            self.memsys.write(parsed_args[0], parsed_args[1])
        elif len(parsed_args) == 3:
            self.memsys.write(parsed_args[0], parsed_args[1], parsed_args[2])
        else:
            print("Too many args")

    def do_show_config(self, args):
        print(f"Address width: {self.address_width}")
        print(f"Set width: {self.set_width}")
        print(f"Way width: {self.way_width}")
        print(f"Line size width: {self.line_size_width}")
        print(f"Memory name: {self.memory_name}")
        print(f"Memory policy: {self.replacement_policy}")
        print(f"Write back: {self.write_back}")
        print(f"Write allocate: {self.write_allocate}")
        print(f"Prefetch blocks: {self.prefetch}")

    def do_show_state(self, args):
        print(f"{Fore.GREEN}{Back.BLUE}Memory State{Style.RESET_ALL}")
        self.memsys.show_state(only_stats=args == "stats")
        
    def do_show_costs(self, args):
        self.memsys.show_costs()

    def parseint(self, oldval, args, name=""):
        try:
            data = int(args)
            print(f"{Fore.GREEN}{name}{Style.RESET_ALL}set to {Fore.YELLOW}{data}{Style.RESET_ALL}")
            return data
        except Exception as e:
            print(e)
            return oldval
    
    def parsebool(self, oldval, args, name=""):
        try:
            data = args == "True"
            print(f"{Fore.GREEN}{name}{Style.RESET_ALL}set to {Fore.YELLOW}{data}{Style.RESET_ALL}")
            return data
        except Exception as e:
            print(e)
            return oldval

    def parsestr(self, oldval, args, name=""):
        try:
            if args is None:
                raise Exception()
            data = str(args)
            print(f"{Fore.GREEN}{name}{Style.RESET_ALL}set to {Fore.YELLOW}{data}{Style.RESET_ALL}")
            return data
        except Exception as e:
            print(e)
            return oldval

    def parsepolicy(self, oldval, args, name=""):
        try:
            data = ReplacementPolicy[str(args)]
            print(f"{Fore.GREEN}{name}{Style.RESET_ALL}set to {Fore.YELLOW}{data}{Style.RESET_ALL}")
            return data
        except Exception as e:
            print(e)
            return oldval

    def do_virtual_address_width(self, args):
        self.virtual_address_width = self.parseint(self.virtual_address_width, args, name="Virtual address width ")
    def do_address_width(self, args):
        self.address_width = self.parseint(self.address_width, args, name="Address width ")
    def do_set_width(self, args):
        self.set_width = self.parseint(self.set_width, args, name="Set width ")
    def do_way_width(self, args):
        self.way_width = self.parseint(self.way_width, args, name="Way width ")
    def do_line_size_width(self, args):
        self.line_size_width = self.parseint(self.line_size_width, args, name="Line size width ")
    def do_prefetch(self, args):
        self.prefetch = self.parseint(self.prefetch, args, name="Prefetch ")
    def do_name(self, args):
        self.memory_name = self.parsestr(self.memory_name, args, name="Memory name ")
    def do_write_back(self, args):
        self.write_back = self.parsebool(self.write_back, args, name="Write back ")
    def do_write_allocate(self, args):
        self.write_allocate = self.parsebool(self.write_allocate, args, name="Write allocate ")
    def do_policy(self, args):
        self.replacement_policy = self.parsepolicy(self.replacement_policy, args, name="Replacement policy ")
    def do_cost_access(self, args):
        self.cost_access = self.parseint(self.cost_access, args, name="Cost access ")
    def do_cost_hit(self, args):
        self.cost_hit = self.parseint(self.cost_hit, args, name="Cost hit ")
    def do_cost_miss(self, args):
        self.cost_miss = self.parseint(self.cost_miss, args, name="Cost miss ")
    def do_cost_through(self, args):
        self.cost_through = self.parseint(self.cost_through, args, name="Cost through ")
    def do_reset_stats(self, args):
        self.memsys.reset_statistics()
        print(f"{Fore.BLUE}Reset statistics{Style.RESET_ALL}")
        
    def do_reset_costs(self, args):
        self.memsys.last_level.reset_costs(cost_hit = self.cost_hit, cost_miss = self.cost_miss, cost_through = self.cost_through, cost_access = self.cost_access)
        print(f"{Fore.BLUE}Reset costs{Style.RESET_ALL}")
        

    def do_create(self, args):
        """create
        Create a memory system with the configured address width and line width
        """
        self.memsys = MemorySystem(self.address_width, self.virtual_address_width)
        print(f"{Fore.BLUE}{Back.GREEN}Created memory system {Fore.RED}{args}{Style.RESET_ALL}")
        
    def do_virtual(self, args):
        """virtual
        Create a virtual memory on top of the existing memory system. 
        Last level must be a cache of line size equal to page size"""
        if self.memsys is None:
            print("Initialize memory first")
        else:
            virmem = VirtualMemory(self.memory_name, self.virtual_address_width, self.address_width, self.line_size_width)
            virmem.add_memory_system(self.memsys)
            #replace the memory system for the virtual one
            self.memsys = virmem
        print(f"{Fore.BLUE}Added virtual memory{Style.RESET_ALL}")    
        

    def do_memory(self, args):
        """memory
        Create the main memory with the configured parameters"""
        if self.memsys is None:
            print("Initialize memory first")
        else:
            try:
                self.memsys.add_main(self.line_size_width, name = self.memory_name)
            except Exception as e:
                print(e)
                return
        print(f"{Fore.BLUE}Added main memory{Style.RESET_ALL}")

    def do_cache(self, args):
        """cache 
        Create a cache level with the configured parameters"""
        if self.memsys is None:
            print("Initialize memory first")
        else:
            try:
                self.memsys.add_cache(name = self.memory_name, set_width = self.set_width, way_width = self.way_width, line_size_width = self.line_size_width, replacement_policy = self.replacement_policy, write_back = self.write_back, write_allocate = self.write_allocate, prefetch = self.prefetch)
            except Exception as e:
                print(e)
                return
        print(f"{Fore.BLUE}Added cache level{Style.RESET_ALL}")

    def do_victim(self, args):
        """victim
        Create a victim cache with the configured parameters"""
        if self.memsys is None:
            print("Initialize memory first")
        else:
            try:
                self.memsys.add_victim(name = self.memory_name, set_width = self.set_width, way_width = self.way_width, line_size_width = self.line_size_width, replacement_policy = self.replacement_policy)
            except Exception as e:
                print(e)
                return
        print(f"{Fore.BLUE}Added victim cache{Style.RESET_ALL}")
    
    def do_quit(self, line):
        return True

    def do_EOF(self, line):
        return True
    
    def postloop(self):
        print

if __name__ == '__main__':
    Cacheasy().cmdloop()
    
    
"""
    write_allocate: reserves memory when writing (brings block)
    no write_allocate: does not reserve memory if the block is not in cache (just writes to upper memory)

    TODO:
    write_back: only write a block when evicted
    write_through: writes all the hierarchy when dirty, no waiting for eviction

    TODO:
    differentiate between line read/writes and word read/writes since it is different!!!
    
"""


        