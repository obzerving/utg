#################################################################################
#                                                                               #
# Universal Tab Generator                                                       #
# Version 1.0                                                                   #
#                                                                               #
# This program generates an SVG file                                            #
#   - Given an SVG file containing a closed path of straight lines              #
#   - Generate a paper model of tabs and score lines for each straight edge     #
#                                                                               #
# Copyright: (c) 2020, Joseph Zakar <observing@gmail.com>                       #
# GNU General Public License v3.0+ (see LICENSE or                              #
# https://tldrlegal.com/license/gnu-general-public-license-v3-(gpl-3)#fulltext) #
#                                                                               #
#################################################################################

# Init variables
import sys
import os
import uuid
from xml.dom.minidom import parse
import xml.dom.minidom
from svgpathtools import *
import math
import tkinter
from tkinter import *
import tkinter.filedialog
import tkinter.font as font
from tkinter import messagebox


# user defaults
inputfile = 'tgtest.svg'
outputfile = 'tgresults.svg'
tab_height = 0.4
dashlength = 0.25

# non-user defaults
orientTop = 0
orientBottom = 1
orientRight = 2
orientLeft = 3
tab_angle = 25.0

def main(argv):
    global orientTop
    global orientBottom
    global orientRight
    global orientLeft
    global tab_height
    global tab_angle
    global inputfile
    global outputfile
    global dashlength

    top = tkinter.Tk()
    top.title("Universal Tab Generator")
    pane = PanedWindow(top, orient=VERTICAL)
    pane.pack(fill=BOTH, expand=1)
    F1 = Frame(pane)
    L1 = tkinter.Label(F1, text="Input File Name   ")
    L1.pack( side = tkinter.LEFT)
    E1 = tkinter.Entry(F1, bd =5, width=30)
    E1.pack(side = tkinter.LEFT)
    F2 = Frame(pane)
    L2 = tkinter.Label(F2, text="Output File Name")
    L2.pack( side = tkinter.LEFT)
    E2 = tkinter.Entry(F2, bd =5, width=30)
    E2.pack(side = tkinter.LEFT)
    F4 = Frame(pane)
    L4 = tkinter.Label(F4, text="Length of Dashline in inches (zero for solid line)")
    L4.pack( side = tkinter.LEFT)
    E4 = tkinter.Entry(F4, bd =5, width=6)
    E4.insert(0,str(dashlength))
    E4.pack(side = tkinter.LEFT)
    F4a = Frame(pane)
    L4a = tkinter.Label(F4a, text="Height of Tab in inches")
    L4a.pack( side = tkinter.LEFT)
    E4a = tkinter.Entry(F4a, bd =5, width=6)
    E4a.insert(0,str(tab_height))
    E4a.pack(side = tkinter.LEFT)
    
    # This is the handler for the input file browse button
    def InfileCallBack():
        ftypes = [('svg files','.svg'), ('All files','*')]
        inputfile = tkinter.filedialog.askopenfilename(title = "Select File", filetypes = ftypes, defaultextension='.svg')
        E1.delete(0,tkinter.END)
        E1.insert(0, inputfile)

    # This is the handler for the output file browse button
    def OutfileCallBack():
        ftypes = [('svg files','.svg'), ('All files','*')]
        outputfile = tkinter.filedialog.asksaveasfilename(title = "Save File As", filetypes = ftypes, defaultextension='.svg')
        E2.delete(0,tkinter.END)
        E2.insert(0,outputfile)

    # This is the handler for the cancel button
    def CancelCallBack():
        top.destroy()

    # This is the handler for the OK button
    def OKCallBack():
        global inputfile
        global outputfile
        global dashlength
        global nohscores
        global tab_height
        inputfile = E1.get()
        outputfile = E2.get()
        dashlength = float(E4.get())
        tab_height = float(E4a.get())
        top.destroy()
      
    dscores = [] # temporary list of all score lines
    opaths = []  # all the generated paths will be stored in this list to write an SVG file
    oattributes = [] # each path in opaths has a corresponding set of attributes in this list
    # attributes for body, top, and bottom
    battributes = {'style' : 'fill:#32c864;stroke:#000000;stroke-width:0.96;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dashoffset:0;stroke-opacity:1'}
    # attributes for scorelines
    sattributes = {'style' : 'fill:none;stroke:#000000;stroke-width:0.96;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dashoffset:0;stroke-opacity:1'}
    B1 = tkinter.Button(F1, text="Browse", command=InfileCallBack)
    B1.pack(side = tkinter.LEFT)
    B2 = tkinter.Button(F2, text="Browse", command=OutfileCallBack)
    B2.pack(side = tkinter.LEFT)
    F6 = Frame(pane)
    bfont = font.Font(size=12)
    B3 = tkinter.Button(F6, text="Cancel", command=CancelCallBack)
    B3['font'] = bfont
    B3.pack(side = tkinter.LEFT, ipadx=30)
    B4 = tkinter.Button(F6, text="OK", command=OKCallBack)
    B4['font'] = bfont
    B4.pack(side = tkinter.RIGHT,ipadx=40)
    pane.add(F1)
    pane.add(F2)
    pane.add(F4)
    pane.add(F4a)
    pane.add(F6)
    top.mainloop()
    # Parse input file into paths, attributes, and svg_attributes
    ipaths, iattributes, isvg_attributes = svg2paths2(inputfile)
    # determine the units and the scale of the input file
    # Check the units to see if we support them
    hwunits = isvg_attributes['height'][-2:]
    if(hwunits != 'in'):
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror('UPC Input Error', 'Document Units Must be in Inches', parent=root)
        sys.exit(6)
    inheight = float(isvg_attributes['height'][:-2])
    inwidth = float(isvg_attributes['width'][:-2])
    invb = isvg_attributes['viewBox'].split()
    # Assumes X and Y scales are equal
    inscale = inwidth/float(invb[2])
    dstr = ipaths[0].d()
    inodes = dstr.split()
    pointype = "XX"
    npath = []
    for coord in range(len(inodes)):
        if inodes[coord] == 'M': # Next two comma separted numbers are first XY point
            pointype = 'M'
        elif inodes[coord] == 'L': # Next two comma separted numbers are XY point to line from last point
            pointype = 'L'
        elif inodes[coord] == 'H': # Next number is X value of a line to last point
            pointype = 'H'
        elif inodes[coord] == 'V': # Next number is Y value of a line to last point
            pointype = 'V'
        elif inodes[coord] == 'Z': # End of path. Nothing after Z
            pointype = 'Z'
        else:
            if (pointype == 'M') or (pointype == 'L'):
                ipoint = inodes[coord].split(',')
            elif pointype == 'H':
                ipoint = inodes[coord]+','+inodes[coord-1].split()[1]
            elif pointype == 'V':
                ipoint = inodes[coord-1].split()[0]+','+inodes[coord]
            x1 = float(ipoint[0])*inscale
            y1 = float(ipoint[1])*inscale
            npath.append(complex(x1, y1))
    # Add tabs to npath
    mpath = [npath[0]]
    for ptn in range(len(npath)-1):
        # Generate score lines
        spaths = makescore(npath[ptn], npath[ptn+1],dashlength)
        dscores.append(spaths)

        if npath[ptn].imag == npath[ptn+1].imag:
            # this will either be a top or bottom tab
            if (npath[ptn].real-npath[ptn+1].real) > 0:
                tpnt = complex(npath[ptn+1].real+0.1, npath[ptn].imag + 0.1)
            else:
                tpnt = complex(npath[ptn].real+0.1, npath[ptn].imag + 0.1)
            if insidePath(npath, tpnt) == 0: # Point is inside the path
                tabpt1, tabpt2 = makeTab(npath[ptn], npath[ptn+1], orientTop) # order of points does not matter
            else:
                tabpt1, tabpt2 = makeTab(npath[ptn], npath[ptn+1], orientBottom)
        elif npath[ptn].real == npath[ptn+1].real:
            # This will either be a right or left tab
            if (npath[ptn+1].imag-npath[ptn].imag) > 0:
                tpnt = complex(npath[ptn+1].real+0.1, npath[ptn].imag + 0.1)
            else:
                tpnt = complex(npath[ptn+1].real+0.1, npath[ptn+1].imag + 0.1)
            if insidePath(npath, tpnt) == 0: # Point is inside the path
                tabpt1, tabpt2 = makeTab(npath[ptn], npath[ptn+1], orientLeft)
            else:
                tabpt1, tabpt2 = makeTab(npath[ptn], npath[ptn+1], orientRight)
        else:
            tabpt1, tabpt2 = makeTab(npath[ptn], npath[ptn+1], orientLeft)
            if insidePath(npath, tabpt1) == 0: # Point is inside the path
                tabpt1, tabpt2 = makeTab(npath[ptn], npath[ptn+1], orientRight)
        mpath.append(tabpt1)
        mpath.append(tabpt2)
        mpath.append(npath[ptn+1])
            
    dprop = 'M'
    for nodes in range(len(mpath)):
        dprop = dprop + ' ' + str(mpath[nodes].real) + ',' + str(mpath[nodes].imag)
    ## and close the path
    dprop = dprop + ' z'
    for dndx in dscores:
        dprop = dprop +dndx
    dpaths = parse_path(dprop)
    opaths.append(dpaths)
    oattributes.append(battributes)
    osvg_attributes = {}
    for ia in isvg_attributes:
        if ((((ia != 'xmlns:dc') and  (ia != 'xmlns:cc')) and (ia != 'xmlns:rdf')) and (ia != 'xmlns:svg')):
            osvg_attributes[ia] = isvg_attributes[ia]
    tmpfile = str(uuid.uuid4())
    totalpaths = Path()
    for tps in opaths:
        totalpaths.append(tps)
    xmin,xmax,ymin,ymax=totalpaths.bbox()
    #wsvg(opaths, attributes=oattributes, svg_attributes=osvg_attributes, filename=tmpfile)
    wsvg(opaths, filename=tmpfile, attributes=oattributes)
    # Post processing stage
    # Due to issues with svgpathtools, some post processing of the file output from the library is necessary until issues have been resolved
    # The following attributes are suitable for input to inkscape and/or the Cricut Design Space
    # Document properties are 11.5 x 11.5 inches. The viewBox sets the scale at 72 dpi. Change the display units in Inkscape to inches.
    docscale = 72
    isvg_attributes = {'xmlns:dc': 'http://purl.org/dc/elements/1.1/', 'xmlns:cc': 'http://creativecommons.org/ns#', 'xmlns:rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'xmlns:svg': 'http://www.w3.org/2000/svg', 'xmlns': 'http://www.w3.org/2000/svg', 'id': 'svg8', 'version': '1.1', 'viewBox': '0 0 828.0 828.0', 'height': '11.5in', 'width': '11.5in'}
    # Assumes order of paths is top, bottom, wrapper, body, scorelines
    ids = ['top','bottom','wrapper','body','scorelines']
    # Read the xml tree from the file
    DOMTree = xml.dom.minidom.parse(tmpfile)
    # Accessing the svg node (which must be the root element)
    svg =DOMTree.documentElement
    # correct the height, width, and viewBox attributes
    svg.setAttribute('height', isvg_attributes['height'])
    svg.setAttribute('width', isvg_attributes['width'])
    svg.setAttribute('viewBox', isvg_attributes['viewBox'])
    # All path nodes under svg
    paths = svg.getElementsByTagName("path")
    wbbox = xmax-xmin
    hbbox = ymax-ymin
    strwidth = isvg_attributes['width']
    if not(strwidth.isdigit()):
        # For now, assume it is a two character unit at the end of the string
        # TODO: Process the units field and modify paths accordingly
        midbbox = (float(strwidth[:-2])-wbbox)/2 -xmin
    else:
        midbbox = (float(strwidth)-wbbox)/2 -xmin
    strheight = isvg_attributes['height']
    if not(strwidth.isdigit()):
        # For now, assume it is a two character unit at the end of the string
        # TODO: Process the units field and modify paths accordingly
        centerbbox = (float(strheight[:-2])-hbbox)/2 -ymin
    else:
        centerbbox = (float(strheight)-hbbox)/2 -ymin
    for p in range(len(paths)):
        # Change paths to close with z rather than repeating first point
        inodes = paths[p].getAttribute('d').split()
        dstr = ''
        firstpoint = ''
        lastpoint = ''
        rplcoord = 0
        process = 1
        for coord in range(len(inodes)):
            if not((inodes[coord] == 'M') or (inodes[coord] == 'L')):
                if firstpoint == '':
                    firstpoint = inodes[coord]
                elif coord == len(inodes)-1: # check last point
                    if inodes[coord] == firstpoint: # does it repeat first point
                        dstr = dstr + 'z' # yes. replace it with a z
                        process = 0 # and stop processing
                    else:
                        ipoint = inodes[coord].split(',')
                        dstr = dstr + cstr + str((float(ipoint[0])+midbbox)*docscale) + ',' + str((float(ipoint[1])+centerbbox)*docscale) + ' '
                        process = 0
                if(process == 1):
                    ipoint = inodes[coord].split(',')
                    dstr = dstr + cstr + str((float(ipoint[0])+midbbox)*docscale) + ',' + str((float(ipoint[1])+centerbbox)*docscale) + ' '
                else:
                    paths[p].setAttribute('d', dstr) # and replace the path
            else:
                cstr = inodes[coord] + ' '
        # Update the path ids to something more meaningful
        paths[p].setAttribute('id',ids[p])
    with open(outputfile,'w') as xml_file:
        DOMTree.writexml(xml_file, indent="\t", newl="\n")
    try:
        os.remove(tmpfile)
    except OSError:
        pass   
    root = tkinter.Tk()
    root.withdraw()
    messagebox.showinfo("UTG", "width = "+str(round(xmax-xmin,3))+", height = "+str(round(ymax-ymin,3)), parent=root)

def insidePath(path, p):
    point = pnPoint((p.real, p.imag))
    pverts = []
    for pnum in path:
        pverts.append((pnum.real, pnum.imag))
    isInside = point.InPolygon(pverts, True)
    if isInside:
        return 0 # inside
    else:
        return 1 # outside

class pnPoint(object):
	def __init__(self,p):
		self.p=p
	def __str__(self):
		return self.p
	def InPolygon(self,polygon,BoundCheck=False):
		inside=False
		if BoundCheck:
			minX=polygon[0][0]
			maxX=polygon[0][0]
			minY=polygon[0][1]
			maxY=polygon[0][1]
			for p in polygon:
				minX=min(p[0],minX)
				maxX=max(p[0],maxX)
				minY=min(p[1],minY)
				maxY=max(p[1],maxY)
			if self.p[0]<minX or self.p[0]>maxX or self.p[1]<minY or self.p[1]>maxY:
				return False
		j=len(polygon)-1
		for i in range(len(polygon)):
			if ((polygon[i][1]>self.p[1])!=(polygon[j][1]>self.p[1]) and (self.p[0]<(polygon[j][0]-polygon[i][0])*(self.p[1]-polygon[i][1])/( polygon[j][1] - polygon[i][1] ) + polygon[i][0])):
				inside =not inside
			j=i
		return inside

def makescore(pt1, pt2, dashlength):
   # Draws a dashed line of dashlength between complex points
   # Assuming pt1y > pt2y
   # Dash = dashlength (in inches) space followed by dashlength mark
   # if dashlength is zero, we want a solid line
   if pt1.imag > pt2.imag:
      apt1 = pt1
      apt2 = pt2
   else:
      apt1 = pt2
      apt2 = pt1
   if dashlength == 0:
      ddash = 'M '+str(apt1.real)+','+str(apt1.imag)+' L '+str(apt2.real)+','+str(apt2.imag)
   else:
      if apt1.imag == apt2.imag:
         # We are drawing horizontal dash lines. Assume pt1x < pt2x
         if pt1.real < pt2.real:
              apt1 = pt1
              apt2 = pt2
         else:
              apt1 = pt2
              apt2 = pt1
         xcushion = apt2.real - dashlength
         ddash = ''
         xpt = apt1.real
         ypt = apt1.imag
         done = False
         while not(done):
            if (xpt + dashlength*2) <= xcushion:
               xpt = xpt + dashlength
               ddash = ddash + 'M ' + str(xpt) + ',' + str(ypt) + ' '
               xpt = xpt + dashlength
               ddash = ddash + 'L ' + str(xpt) + ',' + str(ypt) + ' '
            else:
               done = True
      elif apt1.real == apt2.real:
         # We are drawing vertical dash lines.
         ycushion = apt2.imag + dashlength
         ddash = ''
         xpt = apt1.real
         ypt = apt1.imag
         done = False
         while not(done):
            if(ypt - dashlength*2) >= ycushion:
               ypt = ypt - dashlength         
               ddash = ddash + 'M ' + str(xpt) + ',' + str(ypt) + ' '
               ypt = ypt - dashlength
               ddash = ddash + 'L ' + str(xpt) + ',' + str(ypt) + ' '
            else:
               done = True
      else:
         # We are drawing an arbitrary dash line
         m = (apt1.imag-apt2.imag)/(apt1.real-apt2.real)
         theta = math.atan(m)
         msign = (m>0) - (m<0)
         ycushion = apt2.imag + dashlength*math.sin(theta)
         xcushion = apt2.real + msign*dashlength*math.cos(theta)
         ddash = ''
         xpt = apt1.real
         ypt = apt1.imag
         done = False
         while not(done):
            nypt = ypt - dashlength*2*math.sin(theta)
            nxpt = xpt - msign*dashlength*2*math.cos(theta)
            if (nypt >= ycushion) and (((m<0) and (nxpt <= xcushion)) or ((m>0) and (nxpt >= xcushion))):
               # move to end of space / beginning of mark
               xpt = xpt - msign*dashlength*math.cos(theta)
               ypt = ypt - msign*dashlength*math.sin(theta)
               ddash = ddash + 'M ' + str(xpt) + ',' + str(ypt) + ' '
               # draw the mark
               xpt = xpt - msign*dashlength*math.cos(theta)
               ypt = ypt - msign*dashlength*math.sin(theta)
               ddash = ddash + 'L' + str(xpt) + ',' + str(ypt) + ' '
            else:
               done = True
   return ddash

def makeTab(pt1, pt2, orient):
   global orientTop
   global orientBottom
   global orientRight
   global orientLeft
   global tab_height
   global tab_angle
   switched = 0
   rpt1x = rpt1y = rpt2x = rpt2y = 0.0
   tabDone = False
   currTabHt = tab_height
   currTabAngle = tab_angle
   while not tabDone:
      if (orient == orientTop) or (orient == orientBottom):
         if pt1.real > pt2.real:
            ppt1 = pt2
            ppt2 = pt1
            switched = 1
         else:
            ppt1 = pt1
            ppt2 = pt2
         if orient == orientTop:
            TBset = -1
         elif orient == orientBottom:
            TBset = 1
         tp1 = complex(0, TBset*currTabHt) 
         tp2 = complex(0, TBset*currTabHt)
         rtp1x = tp1.real*math.cos(math.radians(-TBset*currTabAngle)) - tp1.imag*math.sin(math.radians(-TBset*currTabAngle)) + ppt1.real
         rtp1y = tp1.imag*math.cos(math.radians(-TBset*currTabAngle)) + tp1.real*math.sin(math.radians(-TBset*currTabAngle)) + ppt1.imag
         rtp2x = tp2.real*math.cos(math.radians(TBset*currTabAngle)) - tp2.imag*math.sin(math.radians(TBset*currTabAngle)) + ppt2.real
         rtp2y = tp2.imag*math.cos(math.radians(TBset*currTabAngle)) + tp2.real*math.sin(math.radians(TBset*currTabAngle)) + ppt2.imag
      elif (orient == orientRight) or (orient == orientLeft):
         if pt1.imag < pt2.imag:
            ppt1 = pt2
            ppt2 = pt1
            switched = 1
         else:
            ppt1 = pt1
            ppt2 = pt2
         if orient == orientRight:
            TBset = -1
         else: # orient == orientLeft
            TBset = 1
         tp1 = complex(-TBset*currTabHt, 0)
         tp2 = complex(-TBset*currTabHt, 0)
         rtp1x = tp1.real*math.cos(math.radians(TBset*currTabAngle)) - tp1.imag*math.sin(math.radians(TBset*currTabAngle)) + ppt1.real
         rtp1y = tp1.imag*math.cos(math.radians(TBset*currTabAngle)) + tp1.real*math.sin(math.radians(TBset*currTabAngle)) + ppt1.imag
         rtp2x = tp2.real*math.cos(math.radians(-TBset*currTabAngle)) - tp2.imag*math.sin(math.radians(-TBset*currTabAngle)) + ppt2.real
         rtp2y = tp2.imag*math.cos(math.radians(-TBset*currTabAngle)) + tp2.real*math.sin(math.radians(-TBset*currTabAngle)) + ppt2.imag
         # Check for vertical line. If so, we are already done
         if (ppt1.real != ppt2.real):
            slope = (ppt1.imag - ppt2.imag)/(ppt1.real - ppt2.real)
            theta = math.degrees(math.atan(slope))
            # create a line segment from ppt1 to rtp1
            td1 = 'M '+str(ppt1.real)+' '+str(ppt1.imag)+' '+str(rtp1x)+' '+str(rtp1y)
            rrtp1 = parse_path(td1)
            # create a line segment from ppt2 to rtp2
            td2 = 'M '+str(ppt2.real)+' '+str(ppt2.imag)+' '+str(rtp2x)+' '+str(rtp2y)
            rrtp2 = parse_path(td2)
            if orient == orientRight:
               # rotate the points theta degrees
               if slope < 0:
                  rtp1 = rrtp1.rotated(90+theta, ppt1)
                  rtp2 = rrtp2.rotated(90+theta, ppt2)
               else:
                  rtp1 = rrtp1.rotated(-90+theta, ppt1)
                  rtp2 = rrtp2.rotated(-90+theta, ppt2)
            if orient == orientLeft:
               # rotate the points theta degrees
               if slope < 0:
                  rtp1 = rrtp1.rotated(90+theta, ppt1)
                  rtp2 = rrtp2.rotated(90+theta, ppt2)
               else:
                  rtp1 = rrtp1.rotated(-90+theta, ppt1)
                  rtp2 = rrtp2.rotated(-90+theta, ppt2)
            rtp1x = rtp1[0][1].real
            rtp1y = rtp1[0][1].imag
            rtp2x = rtp2[0][1].real
            rtp2y = rtp2[0][1].imag
      if detectIntersect(ppt1.real, ppt1.imag, rtp1x, rtp1y, ppt2.real, ppt2.imag, rtp2x, rtp2y):
         currTabAngle = currTabAngle - 1.0
         if currTabAngle < 2.0:
            currTabHt = currTabHt - 0.1
            currTabAngle = tab_angle
      else:
         tabDone = True
   p1 = complex(rtp1x,rtp1y)
   p2 = complex(rtp2x,rtp2y)
   if switched == 0:
      return p1, p2
   else:
      return p2, p1

def detectIntersect(x1, y1, x2, y2, x3, y3, x4, y4):
   td = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
   if td == 0:
      # These line segments are parallel
      return False
   t = ((x1-x3)*(y3-y4)-(y1-y3)*(x3-x4))/td
   if (0.0 <= t) and (t <= 1.0):
      return True
   else:
      return False
      
if __name__ == "__main__":
   main(sys.argv[1:])# Ensure that arguments are valid
