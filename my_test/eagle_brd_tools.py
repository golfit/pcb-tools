'''
This Python script assembles a few tools useful for creating
Eagle .brd files with objects placed in an algorithmic way.

T. Golfinopoulos, 26 September 2018

See also test_gen_instr_board.py
'''

from abc import ABC,abstractmethod
from numpy import pi,floor,ceil
import numpy
import csv #For creating .csv bill-of-materials

class Xml(ABC) :
    @abstractmethod
    def get_str(self):
        pass
    
    def __repr__(self) :
        return self.get_str()
    
class Part(Xml) :
    def __init__(self,name,x,y) :
        self.name=name
        self.x=x
        self.y=y
    
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self,name):
        self._name=name
    
    @property
    def x(self):
        return self._x
    @x.setter
    def x(self,x):
        self._x=x
    
    @property
    def y(self):
        return self._y
    @y.setter
    def y(self,y):
        self._y=y

class Hole(Part):
    def __init__(self,x,y,drill):
        '''
        Representation of non-plated (i.e. mounting) hole
        name argument is automatically passed "None," since individual hole references
        are not needed (as holes cannot be routed)
        
        x,y=location of hole
        drill=diameter of drill hole
        '''
        super().__init__(None,x,y)
        self.drill=drill
    
    def get_str(self):
        return '<hole x="{:.5f}" y="{:.5f}" drill="{:.5f}"/>\n'.format(self.x,self.y,self.drill)

class Circle(Part):
    def __init__(self,x,y,diameter,width=0.3048,layer=20):
        '''
        Representation of circle shape (i.e. milled boundary)
        No name
        
        x,y=center of circle
        diameter=diameter of circle
        width=width of line (default=0.3048, i.e. 0.012" in mm)
        layer=number (ID) of layer on which to place circle.  Default=20 (board dimension - i.e. if you want to bound board with circle); top silkscreen=21
        '''
        super().__init__(None,x,y)
        self.diameter=diameter
        self.layer=layer
        self.width=width
    
    def get_str(self):
        return '<circle x="{:.5f}" y="{:.5f}" radius="{:.5f}" width="{:.5f}" layer="{}"/>\n'.format(self.x,self.y,self.diameter/2,self.width,self.layer)

class Wire(Xml):
    def __init__(self,x1,y1,x2,y2,width=0.3048,layer=1,curve=None):
        '''
        Representation of wire 
        
        x1,y1=starting point of wire
        x2,y2=end point of wire
        width=width of wire, default=0.3048 (i.e. 0.012" in mm)
        layer=layer of wire.  Default=1 (top copper); 21=top silkscreen
        curve=number of degrees of curvature between x1,y1 and x2,y2.  Positive for counter-clockwise, 1 to 2, negative for counterclockwise (?)
        '''
        self.x1=x1
        self.y1=y1
        self.x2=x2
        self.y2=y2
        self.width=width
        self.layer=layer
        self.curve=curve
    
    def get_str(self):
        rep_str='<wire x1="{:.5f}" y1="{:.5f}" x2="{:.5f}" y2="{:.5f}" width="{:.5f}" layer="{}"'.format(self.x1,self.y1,self.x2,self.y2,self.width,self.layer)
        if not self.curve is None :
            rep_str+=' curve="{}"'.format(self.curve)
        return rep_str+'/>\n'
class Pad(Part) :
    def __init__(self,name,x,y,diameter,rotation=0,\
                drill=0,shape="round",\
                thermals=True,stop=True,first=False):
        '''
        Initialize class to represent pad.
        
        Usage:
            my_pad=Pad(name,x,y,[diameter,drill,shape,thermals])
            name=String, reference ID for pad-often a number, e.g. "1"
            x,y = center point of pad.
            diameter = general dimension of part
            rotation = rotation angle (counter-clockwise) in degrees between R0 and R359.9.  Default=0
            drill=diameter of drill hole.  Default=0
            shape=a string, must be "square, round, octagon, long, offset" - default=round
            thermals=Boolean flag indicating whether or not pad has thermal breaks.  Default=False
            stop=Boolean flag (?) Default=True           
            first=Boolean flag (?) Default=True
            
        
        T. Golfinopoulos, 26 September 2018
        '''
        super().__init__(name,x,y)
        self.diameter=diameter
        self.rotation=rotation
        self.drill=drill
        self.shape=shape
        self.thermals=thermals
        self.stop=stop
        
    @property
    def diameter(self):
        return self._diameter
    @diameter.setter
    def diameter(self,diameter):
        if diameter<0:
            raise ValueError("Diameter must be > 0 - value entered={}".format(diameter))
        else :
            self._diameter=diameter
    
    @property
    def thermals(self):
        if self._thermals :
            return 'yes'
        else :
            return 'no'
                
    @thermals.setter
    def thermals(self,thermals):
        self._thermals=thermals
    
    @property
    def stop(self):
        if self._stop :
            return 'yes'
        else :
            return 'no'
                
    @stop.setter
    def stop(self,stop):
        self._stop=stop
    
    @property
    def first(self):
        if self._first :
            return 'yes'
        else :
            return 'no'
                
    @first.setter
    def stop(self,first):
        self._first=first
        
    def get_str(self):
        '''
        Return pad xml string for .brd file
        
        T. Golfinopoulos, 26 Sep. 2018
        '''
        return '<pad name="{}" x="{:.5f}" y="{:.5f}" diameter="{:.5f}" rot="R{:.5f}" drill="{:.5f}" shape="{}" thermals="{}" stop="{}" first="{}"/>\n'.format(\
                self.name,self.x,self.y,self.diameter,self.rotation,self.drill,self.shape,self.thermals,self.stop,self.first)
            
class Via(Part):
    def __init__(self,name,x,y,drill,extent='1-16'):
        super().__init__(name,x,y)
        self.drill=drill
        self.extent=extent
    def get_str(self):
        return '<via name="{}" x="{:.5f}" y="{:.5f}" drill="{:.5f}" extent="{}">\n'.format(self.name,self.x,self.y,self.drill,self.extent)
        
class Smd(Part):
    def __init__(self,name,x,y,dx,dy,layer,rotation=0,roundness=0,stop=True,thermals=True,cream=True):
        '''
        Class to represent surface-mount pad
        
        x,y=center position of part
        dx,dy=width and height of part (extent in x and y)
        layer=which print layer to put smd
        rotation=rotation angle in degrees counterclockwise.  Default=R0 (0 degrees).
        roundness=integer parameter between 0 and 100.  0 results in fully rectangular smd, while 100 makes corners of smd fully round.  Default=0.
        stop=?
        thermals=?presumably something to do with thermal breaks in pads
        cream=?
        
        26 Sep. 2018, T. Golfinopoulos
        '''
        super().__init__(name,x,y)
        self.rotation=rotation
        self.dx=dx
        self.dy=dy
        self.layer=layer
        self.roundness=roundness
        self.stop=stop
        self.thermals=thermals
        self.cream=cream
        
    @property
    def cream(self):
        if self._cream :
            return 'yes'
        else :
            return 'no'
    
    @cream.setter
    def cream(self,cream):
        self._cream=cream
        
    @property
    def thermals(self):
        if self._thermals :
            return 'yes'
        else :
            return 'no'
    
    @thermals.setter
    def thermals(self,thermals):
        self._thermals=thermals
        
    @property
    def stop(self):
        if self._stop :
            return 'yes'
        else :
            return 'no'
    
    @stop.setter
    def stop(self,stop):
        self._stop=stop
        
    def get_str(self):
        return '<smd name="{}" x="{:.5f}" y="{:.5f}" rot="R{:.5f}" dx="{:.5f}" dy="{:.5f}" layer="{}" roundness="{}" stop="{}" thermals="{}" cream="{}"/>\n'.format(self.name,self.x,self.y,self.rotation,self.dx,self.dy,self.layer,self.roundness,self.stop,self.thermals,self.cream)

class Text:
    def __init__(self,x,y,size,layer,text,rotation=0,font='proportional',distance=50,align='bottom-left',ratio=8,mirror=False):
        self.x=x
        self.y=y
        self.rotation=rotation
        self.align=align
        self.distance=distance
        self.font=font
        self.layer=layer
        self.ratio=ratio
        self.size=size
        self.text=text
        self.mirror=mirror
    def get_str(self):
        if self.mirror :
            mirror_str='M'
        else :
            mirror_str=''
        return '<text x="{:.5f}" y="{:.5f}" size="{:.5f}" layer="{}" rot="{}R{:.5f}" ratio="{}" font="{}" distance="{}" align="{}">{}</text>\n'.format(self.x,self.y,self.size,self.layer,mirror_str,self.rotation,self.ratio,self.font,self.distance,self.align,self.text)

class LibraryPackage(Xml) :
    def __init__(self,name,library=None,description=None):
        '''
        A class of part (plays role of, e.g., a macro in a Gerber file,
        of which copies may be flashed (stamped) on the board at
        different locations and rotations).
        
        name=name (string ID) of part
        library=instance of Library class to which this part belongs.  (Default=None)
        '''
        self.name=name
        self.library=library
        
        self.description=description

        self.piece_dict={} #
    
    def set_library(self,library):
        self.library=library
    
    def get_pieces(self):
        return self.piece_dict
    
    def get_piece(self,name):
        return self.piece_dict[name][1]
    
    def get_piece_x(self,name):
        return self.get_piece(name).x

    def get_piece_y(self,name):
        return self.get_piece(name).y
    
    def get_lib_name(self):
        return self.library.name
        
    def get_lib_urn(self):
        return self.library.urn
    
    def get_lib_version(self):
        return self.library.version
    
    def add_piece(self,piece):
        #self.pieces.append(piece)
        self.piece_dict[piece.name]=(len(self.piece_dict),piece)
    
    def get_str(self):
        out='<package name="{}" library_version="{}">\n'.format(self.name,self.get_lib_version())
        if not self.description is None :
            out+='<description>{}</description>\n'.format(self.description)
        #Sort pieces by order in which they were added
        pieces=list(self.piece_dict.values())
        pieces_sort=['']*len(pieces)
        for i in range(len(pieces)):
            pieces_sort[pieces[i][0]]=pieces[i][1]

        for p in pieces_sort:
            out+=p.get_str()
        out+='</package>\n'
        return out

class Element(Part):
    def __init__(self,name,package,x,y,rotation,value="",mirror=False):
        '''
        Board instance of an instance of LibraryPackage (i.e. LibraryPackage specifies a class of part, and element is an instance of that class).
        
        name=string ID of element - example: "E$1"
        library=library name (string) that part belongs to
        library_urn=urn reference of library
        package=instance of the LibraryPackage of which this element is an instance.
        x,y=location of part on board
        value=Not sure - default is empty string, ""
        mirror=whether part should be mirrored to, e.g., bottom of board (text will appear backward from top-down view).  Boolean, default=false
        
        T. Golfinopoulos, 27 September 2018
        '''
        super().__init__(name,x,y)
        self.package=package
        self.package_name=package.name
        self.library=package.get_lib_name()
        self.library_urn=package.get_lib_urn()
        self.rotation=rotation
        self.value=value
        self.mirror=mirror
        
    def get_pads(self):
        return self.package.get_pieces()
    
    def get_pad_names(self):
        return self.package.get_pieces().keys()
    
    def get_pad_x(self,pad_name):
        '''
        Get x location of a named pad, acounting for element rotation.
        '''
        #Rotation transform:
        #x=numpy.cos(a*pi/180)*x-numpy.sin(a*pi/180)*y
        #y=numpy.sin(a*pi/180)*x+numpy.cos(a*pi/180)*y
        return self.x+numpy.cos(self.rotation*pi/180)*self.package.get_piece_x(pad_name)-numpy.sin(self.rotation*pi/180)*self.package.get_piece_y(pad_name)
    
    def get_pad_y(self,pad_name):
        '''
        Get y location of a named pad, accounting for element rotation.
        '''
        #Rotation transform:
        #x=numpy.cos(a*pi/180)*x-numpy.sin(a*pi/180)*y
        #y=numpy.sin(a*pi/180)*x+numpy.cos(a*pi/180)*y
        return self.y+numpy.sin(self.rotation*pi/180)*self.package.get_piece_x(pad_name)+numpy.cos(self.rotation*pi/180)*self.package.get_piece_y(pad_name)
        
    def get_str(self):
        #An "M" before rotation field causes part to be mirrored
        if self.mirror :
            mirror_str="M"
        else :
            mirror_str=""
        
        out='<element name="{}" library="{}" library_urn="{}" package="{}" value="{}" x="{:0.5f}" y="{:0.5f}" rot="{}R{:0.5f}"/>\n'.format(self.name,self.library,self.library_urn,self.package_name,self.value,self.x,self.y,mirror_str,self.rotation)
        return out

class Signal(Xml):
    def __init__(self,name,elem1,pad1,elem2,pad2,layer,elems=None,airwireshidden=False):
        '''
        name=name of signal (string).  Example: S$1
        elem1=instance of Element object to which first pad belongs
        pad1=name (string) of pad in elem1 where signal starts
        elem2=instance of Element object to which second pad belongs
        pad2=name (string) of pad in elem2 to which signal connects
        elems=list of additional tuples containing (elem,pad).  Default=None
        airwireshidden=optional input, boolean, default=True
        '''
        self.name=name
        self.elems=[(elem1,pad1),(elem2,pad2)]
        self.layer=layer
        if not elems is None :
            self.elems+=elems
        self.airwireshidden=airwireshidden

    @property
    def airwireshidden(self):
        if self._airwireshidden :
            return 'yes'
        else :
            return 'no'
    
    @airwireshidden.setter
    def airwireshidden(self,airwireshidden):
        self._airwireshidden=airwireshidden
        
    def get_str(self):
        out='<signal name="{}" airwireshidden="{}">\n'.format(self.name,self.airwireshidden)
        for e in self.elems :
            #Put name of each element and pad
            out+='<contactref element="{}" pad="{}"/>\n'.format(e[0].name,e[1])
        
        #Place wires
        for i in range(1,len(self.elems)):
            out+='<wire x1="{}" y1="{}" x2="{}" y2="{}" width="0" layer="{}"/>\n'.format(\
                self.elems[i-1][0].get_pad_x(self.elems[i-1][1]),\
                self.elems[i-1][0].get_pad_y(self.elems[i-1][1]),\
                self.elems[i][0].get_pad_x(self.elems[i][1]),\
                self.elems[i][0].get_pad_y(self.elems[i][1]),\
                self.layer)
        out+='</signal>\n'
        return out

class Library(Xml) :
    def __init__(self,name,urn,description=None,version=1):
        '''
        Create a library, adding packages (parts)
        
        name=name of library (string)
        urn=some kind of library ID, perhaps with path (string)
        description=string descriptor of library.  Default=None
        version=version number of library (default=1)
        '''
        self.name=name
        self.urn=urn
        self.description=description
        self.packages=[] #Initialize package list
        self.version=version
    
    def add_package(self,package):
        '''
        Add library packages to instance list
        my_library.add_package(my_package)
        my_package should be of type, LibraryPackage
        '''
        
        if not type(package) is LibraryPackage :
            raise ValueError("input must be a LibraryPackage - type of input is {}".format(type(package)))
        
        #Ensure that this library is referenced by part
        package.set_library(self)
        
        self.packages.append(package)
    
    def get_str(self):
        '''
        Return xml string for library, adding all parts
        '''
        out='<library name="{}" urn="{}">\n'.format(self.name,self.urn)
        if not self.description is None :
            out+='<description>{}</description>\n'.format(self.description)
        out+='<packages>\n'
        #Insert all packages from library
        for p in self.packages:
            out+=p.get_str()
        out+='</packages>\n'
        out+='</library>\n'
        return out

class BrdFile:
    def __init__(self,title=None,units='mm',grid_distance=0.5,alt_distance=0.1,header_comments=None,brd_width=400,brd_height=400):
        '''
        Initialize BrdFile object with header information.
        Usage:
        title=String appearing on first-line comment of Gerber file.  Default=None
        units=string, either "mm" or "in"
        grid_distance=spacing (in unit) between grid points.  Default=0.5
        alt_distance=spacing (in unit) between alternate grid points (hold down "Alt" key to access alternate grid).  Default=0.1
        
        my_gerber_file=GerberFile(title,units='mm',grid_dist=0.5,altdistance="0.1" x_prec_dec=4,y_prec_int=3,y_prec_dec-4,header_comments=None)
        
        header_comments=String or array of strings to placed in header after title
        
        T. Golfinopoulos, 26 September 2018
        '''
        self.title=title
        self.units=units
        self.grid_distance=grid_distance
        self.alt_distance=alt_distance
        self.header_comments=header_comments
        
        #Prepare lists of libraries and elements
        self.libraries=[]
        self.elements=[]
        self.signals=[]
        self.plain=[]
        
    @property
    def units(self):
        return self._units
    
    @units.setter
    def units(self,units):
        err_msg='units must be a string, and either "mm" or "in"'
        if not type(units) is str :
            raise ValueError(err_msg)
        if not (units.lower()=='mm' or units.lower()=='in') :
            raise ValueError(err_msg)
        self._units=units
        
    @property
    def grid_distance(self):
        return self._grid_distance
    
    @grid_distance.setter
    def grid_distance(self,grid_distance):
        self._grid_distance=grid_distance
        
    @property
    def alt_distance(self):
        return self._alt_distance
    
    @alt_distance.setter
    def alt_distance(self,alt_distance):
        self._alt_distance=alt_distance
    
    def get_header(self):
        '''
        Return string in Eagle xml format, including
        xml version, DOCTYPE, eagle version, <drawing>, settings,
        and ending with <grid .../>
        
        T. Golfinopoulos, 26 Sep. 2018
        '''
        output='<?xml version="1.0" encoding="utf-8"?>\n'
        output+='<!DOCTYPE eagle SYSTEM "eagle.dtd">\n'
        output+='<!--{}-->\n'.format(self.title)
        output+='<!--{}-->\n'.format(self.header_comments)
        output+='<eagle version="9.1.3">\n'
        output+='<drawing>\n'
        output+='<settings>\n'
        output+='<setting alwaysvectorfont="no"/>\n'
        output+='<setting verticaltext="up"/>\n'
        output+='</settings>\n'
        output+='<grid distance="{}" unitdist="{}" unit="{}" style="dots" multiple="1" display="yes" altdistance="{}" altunitdist="{}" altunit="{}"/>\n'.format(self.grid_distance,self.units,self.units,self.alt_distance,self.units,self.units)
        
        #Add one line of white space
        output+='\n'
        
        #Return header
        return output
    
    def get_end(self):
        output='<mfgpreviewcolors>\n'
        output+='<mfgpreviewcolor name="soldermaskcolor" color="0xC8008000"/>\n'
        output+='<mfgpreviewcolor name="silkscreencolor" color="0xFFFEFEFE"/>\n'
        output+='<mfgpreviewcolor name="backgroundcolor" color="0xFF282828"/>\n'
        output+='<mfgpreviewcolor name="coppercolor" color="0xFFFFBF00"/>\n'
        output+='<mfgpreviewcolor name="substratecolor" color="0xFF786E46"/>\n'
        output+='</mfgpreviewcolors>\n'
        output='</board>\n'
        output+='</drawing>\n'
        output+='</eagle>'
        return output
    
    def add_signal(self,signal):
        if not type(signal) is Signal :
            raise ValueError("Error - input must be of type, Signal; type of this input is {}".format(type(signal)))
        self.signals.append(signal)
    
    def add_library(self,library):
        if not type(library) is Library :
            raise ValueError("Error - input must be of type, Library; type of this input is {}".format(type(library)))
        self.libraries.append(library)
    
    def add_element(self,element):
        if not type(element) is Element :
            raise ValueError("Error - input must be of type, Element; type of this input is {}".format(type(element)))
        self.elements.append(element)
    
    def add_plain(self,part):
        '''
        Add a plain geometric object, like a hole or rectangle
        '''
        self.plain.append(part)
    
    def make_brd(self):
        '''
        Return a string containing the whole .brd file
        '''
        out=self.get_header()
        
        #Add layers
        #f=open('layers.xml')
        new_path='/media/golfit/ea24140b-6ec6-4bf6-9f7b-1f3dea715e4d/golfit/git/pcb-tools/my_test'
        f=open('{:s}/layers.xml'.format(new_path))
        out+=f.read()
        f.close()
        
        #Start board
        out+='<board>\n'
                
        #Add plain objects
        out+='<plain>\n'
        for p in self.plain :
            out+=p.get_str()    
        out+='</plain>\n'
        
        #Add libraries
        out+='<libraries>\n'
        #Add connector libraries
        f=open(new_path+'/connector_library.xml')
        out+=f.read()
        f.close()
        #Add all local libraries
        for l in self.libraries:
            out+=l.get_str()
        out+='</libraries>\n'
        
        #Add attributes, including design rules, routing rules, etc.
        attributes_file=open(new_path+'/brd_attributes.xml')
        out+=attributes_file.read()
        attributes_file.close()
        
        #Add elements
        out+='<elements>\n'
        for e in self.elements:
            out+=e.get_str()
        out+='</elements>\n'
        
        #Add signals
        out+='<signals>\n'
        for s in self.signals :
            out+=s.get_str()
        out+='</signals>\n'
        out+=self.get_end()
        return out

    def make_bom(self,fname='bom.csv',heading=None):
        '''
        Generate a bill-of-materials (BOM) from elements.  Write to csv.  Delimeter is semicolon (;).
        
        make_bom(self,fname='bom.csv',heading=None):
        
        fname=filename into which bill of materials will be written.  Must end with .csv file extension.  Default="bom.csv"
        heading=Header information that will appear at top of BOM, e.g. project title, name, contact info, etc.  String or None.  Default=None.
        
        USAGE:
        my_brd.make_bom()
        my_brd.make_bom('my_bom.csv')
        my_brd.make_bom('my_bom.csv','Project 3\nJohn Doe\nPhone: 555-5555')
        
        TG, 9 Dec. 2018
        '''
        if fname[-4:] != '.csv':
            raise ValueError('File name extension must be .csv - you entered file name, {}'.format(fname))
            
        #Find all unique element varieties 
        #Each element is an instance of a particular package
        #Each element instance has a unique name
        unique_packages=[]
        package_map=[]
        elem_map=[]
        for e in self.elements :
            if not e.package_name in unique_packages :
                unique_packages.append(e.package_name)
                package_map.append((e.package_name,[]))
                elem_map.append((e.package_name,[]))
        
        package_map=dict(package_map)
        elem_map=dict(elem_map) #Map instances of elements by package name
        
        for e in self.elements :
            package_map[e.package_name].append(e.name) #Add part designation to map
            elem_map[e.package_name].append(e) #Add part designation to map
        
        csvfile=open(fname, 'w', newline='')
        bomwriter = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        
        bom_col_names=['Item #','Qty Per Board','Ref Des.','Manufacturer',\
                       'Mfg Part #','Description','Package	Type','# of leads','Shipped Inventory']
        
        #spamwriter.writerow(['Spam'] * 5 + ['Baked Beans'])
        #spamwriter.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])

        bomwriter.writerow([self.title]) #Write title
        if not heading is None :
            bomwriter.writerow([heading])

        bomwriter.writerow(['']) #Empty row, spacing
        
        #Write column headings
        bomwriter.writerow(bom_col_names)
        
        #Add a row for each unique part
        for i in range(len(unique_packages)):
            row_data=[] #Initialize row data
            row_data.append(i+1) #Item # - start counting at 1
            row_data.append(len(package_map[unique_packages[i]])) #Number if pieces of this part
            row_data.append(', '.join(package_map[unique_packages[i]])) #Part designators in comma-separated list
            row_data.append('') #Manufacturer - not recorded
            row_data.append('') #Manufacturer part number - not recorded
            row_data.append('') #Description - not recorded
            row_data.append(unique_packages[i]) #Name of package
            row_data.append(len(elem_map[unique_packages[i]][0].get_pads())) #Number of leads
            row_data.append('') #Shipped inventory - not recorded
            
            bomwriter.writerow(row_data) #Add row of data
            
        #Close BOM file
        csvfile.close()
        
        msg="BOM written to "+fname
        print("="*len(msg)+'\n'+msg+"\n"+"="*len(msg))
