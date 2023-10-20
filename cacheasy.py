from enum import Enum
import numpy as np

rng = np.random.default_rng()

ReplacementPolicy = Enum('ReplacementPolicy', ['FIFO', 'LRU', 'MRU', 'RANDOM'])

class MainMemory:

    def __init__(self, address_width, line_size_width, name = "Main memory"):
        self.name = name
        self.address_width = address_width
        self.line_size_width = line_size_width
        

    def read_address(self, addr):
        print(prettydir(addr, self.address_width, 0, self.line_size_width) + " " + prettydown + " Block read from main memory")
        return True

    def write_address(self, addr):
        print(prettydir(addr, self.address_width, 0, self.line_size_width) + " " + prettyup + " Block written to main memory")
        return True



        

class CacheSet:

    def __init__(self, way_width, replacement_policy, tag_width = 32):
        self.way_width = way_width
        self.replacement_policy = replacement_policy
        self.tag_width = tag_width
        self.lines = []
        for i in range(2**way_width):
            self.lines.append(CacheLine(0, valid=False, tag_width = tag_width))


    def contains(self, tag):
        for line in self.lines:
            if line.valid and line.tag == tag:
                return True
                
        return False


    def read(self, tag):
        for (i, line) in enumerate(self.lines):
            if line.valid and line.tag == tag:
                match self.replacement_policy:
                    case ReplacementPolicy.LRU | ReplacementPolicy.MRU:
                        elem = self.lines.pop(i)
                        self.lines.insert(0, elem)
                    case _:
                        pass
                        #doesnt matter for the rest
                return True
        return False

    #assumes the element is not in the set
    #and puts it if it fits. If it does not, it evicts a block and returns it
    def put(self, tag):
        if self.contains(tag):
            print("ERROR: adding existing element to cache set")
            exit()

        #force space to be allocated (None if not needed)
        #outgoing = self.allocate_for(tag)

        match self.replacement_policy:
            case ReplacementPolicy.RANDOM:
                placed = False
                for (i, elem) in enumerate(self.lines):
                    if not elem.valid:
                        elem = CacheLine(tag, tag_width = self.tag_width)
                        placed = True
                        break

                if not placed:
                    #chech that last element is invalid
                    if self.lines[-1].valid:
                        print("ERROR")
                        exit()
                    self.lines[-1] = CacheLine(tag, tag_width = self.tag_width)
            case _:
                #chech that first element is invalid
                if self.lines[0].valid:
                    print("ERROR")
                    exit()
                self.lines[0] = CacheLine(tag, tag_width = self.tag_width)
        #return outgoing
        
    def allocate_for(self, tag):
        if self.contains(tag):
            print("ERROR: allocating for itself")
            exit()
        
        outgoing = None
        match self.replacement_policy:
            case ReplacementPolicy.RANDOM:
                index = rng.randint(0, 2**self.way_width-1)
                outgoing = self.lines[index]
                self.lines[index] = None
            case ReplacementPolicy.FIFO | ReplacementPolicy.LRU:
                outgoing = self.lines.pop()
                #self.lines[-1] = CacheLine(0, valid=False);
                self.lines.insert(0, CacheLine(0, valid=False, tag_width = self.tag_width))
            case ReplacementPolicy.MRU:
                outgoing = self.lines.pop(0)
                #self.lines.append(CacheLine(0, valid=False))
                self.lines.push(CacheLine(0, valid=False, tag_width = self.tag_width))
            case _:
                print("ERROR: using an unsupported policy")
                exit()

        return outgoing

                
    #assume the element is already in the set!!
    def write(self, tag):
        for (i, line) in enumerate(self.lines):
            if line.tag == tag:
                match self.replacement_policy:
                    case ReplacementPolicy.LRU | ReplacementPolicy.MRU:
                        elem = self.lines.pop(i)
                        elem.dirty = True
                        self.lines.insert(0, elem)
                    case _:
                        pass
                        #doesnt matter for the rest
                return True
        return False

    def __str__(self):
        tags = []
        for line in self.lines:
            tags.append(str(line))

        return "[" + ",".join(tags) + "]" 


class CacheLine:

    def __init__(self, tag, valid = True, tag_width = 32):
        self.dirty = False
        self.tag = tag
        self.valid = valid
        self.tag_width = tag_width

    def __str__(self):
        string = prettydir(self.tag, self.tag_width, 0, 0, brackets = False)
        string += (Fore.BLACK if not self.valid else Fore.GREEN) + "V" + Style.RESET_ALL
        string += (Fore.BLACK if not self.dirty else Fore.YELLOW) + "D" + Style.RESET_ALL
        return string
        #return "" + str(self.tag) + ":" + str(self.dirty) + ":" + str(self.valid)



class Cache:
    #TODO: Add victim caches, 

    def __init__(self, name, set_width, way_width, line_size_width, replacement_policy = ReplacementPolicy.LRU, write_back = True, write_allocate = True, load_from = None, store_to = None, address_width = 32):
        self.replacement_policy = replacement_policy
        self.set_width = set_width #number of distinct sets of blocks. 1 set means fully associative
        self.way_width = way_width #number of blocks per set. 1 way means directly mapped
        self.line_size_width = line_size_width
        self.write_back = write_back
        self.write_allocate = write_allocate
        self.load_from = load_from
        self.store_to = store_to
        self.address_width = address_width

        self.name = name

        #initialize set dictionary
        self.set_data = []
        for i in range(2**self.set_width):
            self.set_data.append(CacheSet(self.way_width, self.replacement_policy, self.address_width - self.line_size_width - self.set_width))

    def get_set(self, addr):
        block = addr >> self.line_size_width
        set_num = block % (2**self.set_width)
        return self.set_data[set_num]
    
    def get_tag(self, addr):
        block = addr >> self.line_size_width
        tag_num = block >> self.set_width
        return tag_num


    def get_block(self, addr):
        candidate_set = self.get_set(addr)
        candidate_tag = self.get_tag(addr)
        if (candidate_set.contains(candidate_tag)):
            #success
            print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettytick + " Tag %d in %s" % (candidate_tag, self.name))
        else:
            
            print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyfail + " Tag %d not in %s" % (candidate_tag, self.name))

            #TODO first check if the evicted tag gonna be dirtied and push it up, THEN pull down new data
            outgoing = candidate_set.allocate_for(candidate_tag)
            if outgoing.valid and outgoing.dirty:
                #TODO push up to higher memory to save (should always be present as it is coherent)
                outgoing_base_addr = ((outgoing.tag << self.set_width) + candidate_tag) << self.line_size_width
                #TODO update block above
                print(prettydir(outgoing_base_addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyright +  " Tag %d from %s to %s" % (outgoing.tag, self.name, self.store_to.name))
                self.store_to.write_address(outgoing_base_addr)

            #TODO request also to victim cache if present
            #if data is not present, request it to higher levels of cache. If it can't get it, bad
            if not self.load_from.read_address(addr):
                return False

            candidate_set.put(candidate_tag)

            print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyleft + " Tag %d from %s to %s" % (candidate_tag, self.load_from.name, self.name))


    def read_address(self, addr):
        self.get_block(addr)
        self.get_set(addr).read(self.get_tag(addr))
        #print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettytick + " Data read at %s" % self.name)
        return True
        
    def write_address(self, addr):
        self.get_block(addr)
        self.get_set(addr).write(self.get_tag(addr))
        #print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettytick + " Data written at %s" % self.name)
        return True

    def __str__(self):
        setstr = []
        for (i, seti) in enumerate(self.set_data):
            setstr.append(str(seti) + " " + prettydir(i << self.line_size_width, self.line_size_width + self.set_width, self.set_width, self.line_size_width))
                        
        return "\n".join(setstr)
        


from colorama import Fore, Style
def prettydir(addr, totalbits, setbits, bytebits, brackets=True):
    
    #calculate the toal amount of bits
    blockbits = totalbits - setbits - bytebits
    #convert addr to binary string of (totalbits)
    binstring = format(addr, '0'+str(totalbits)+'b')
    #separate bits
    blockstr = binstring[:blockbits]
    setstr = binstring[blockbits:blockbits+setbits]
    bytebits = binstring[blockbits+setbits:]

    if brackets:
        return '[' + Fore.RED + blockstr + Fore.GREEN + setstr + Fore.BLUE + bytebits + Style.RESET_ALL + ']'
    else:
        return Fore.RED + blockstr + Fore.GREEN + setstr + Fore.BLUE + bytebits + Style.RESET_ALL
    
prettytick = Fore.GREEN + "✔" + Style.RESET_ALL
prettyfail = Fore.RED + "✘" + Style.RESET_ALL
prettyright = Fore.YELLOW + "→" + Style.RESET_ALL
prettyleft = Fore.YELLOW + "←" + Style.RESET_ALL
prettyup = Fore.BLUE + "↑" + Style.RESET_ALL
prettydown = Fore.BLUE + "↓" + Style.RESET_ALL

import time

def main():
    line_size_width = 4
    address_width = 16
    set_width = 2 # 4 sets
    way_width = 1 # 2 ways

    mem = MainMemory(address_width = address_width, line_size_width = line_size_width)
    cache = Cache("L1", set_width, way_width, line_size_width = line_size_width, replacement_policy = ReplacementPolicy.LRU, load_from = mem, store_to = mem, address_width = address_width)

    """for i in range(1000):
        if np.random.randint(2) > 0:
            cache.read_address(np.random.randint(2**15))
        else:
            cache.write_address(np.random.randint(2**15))
        time.sleep(0.2)"""

    cache.read_address(0x2001)
    cache.read_address(0x2002)
    cache.write_address(0x2003)

    cache.write_address(0x3003)
    cache.read_address(0x4003)

    print(cache)

    print(format(2, '0'+str(20)+'b'))


main()




"""
TODOS:
    Pretty print cache structure with what's inside and such
    Add timing statistics somewhere
    Add victim cache
"""

#todo estabas haciendo que el cacheset tenga un array de tamaño fijo para las vías!!! (así se imprime siempre todo)
#habrá que cambiar los algoritmos de reemplazo para que busquen Nones