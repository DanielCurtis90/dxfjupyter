import ezdxf
import csv, copy
import os

def lwpolyline_points(entity):
	coord_list = []
	for poly_point in entity.get_points():
		for coord in poly_point:
			coord_list.append(coord)
	return coord_list

class VERTEX:
	def __init__(self, vertex_info):
		self.xpoint = vertex_info[0]
		self.ypoint = vertex_info[1]
		if len(vertex_info) > 3:
			self.startw = vertex_info[2]
			self.endw = vertex_info[3]
			self.bulge = vertex_info[4]

def zero_and_round(vertex_list):
	x_coords = []
	y_coords = []
	for vertex in vertex_list:
		x_coords.append(vertex.xpoint)
		y_coords.append(vertex.ypoint)
	#For each entry in these x or y coordinate lists, increase them by the absolute value of the lowest negative number
	#This zeroes the coordinate system. Then round them to 3 decimal places. 
	#Only do this if the lowest number in the x or y coordinate list is a negative!
	shiftx_coords = [round(x + abs(min(x_coords)), 3) if min(x_coords) < 0 else round(x, 3) for x in x_coords]
	shifty_coords = [round(y + abs(min(y_coords)), 3) if min(y_coords) < 0 else round(y, 3) for y in y_coords]
	#Reassign the shifted coordinates
	for counter, vertex in enumerate(vertex_list):
		vertex.xpoint = shiftx_coords[counter]
		vertex.ypoint = shifty_coords[counter]
	return vertex_list

class LWPOLYLINE:
	def __init__(self, entity):
		#As the amount of vertices in a LWPOLYLINE can be any number, we need to create a list
		vertices = []
		#Returns a list of vertex information (another list)
		for point in entity.get_points():
			vertices.append(VERTEX(point))
		raw_vertices = copy.deepcopy(vertices)
		self.vertices = raw_vertices
		self.zeroed_vertices = zero_and_round(vertices)
		self.layer = entity.dxf.layer
		self.handle = entity.dxf.handle
		self.type = entity.dxftype()

class LINE:
	def __init__(self, entity):
		#As the amount of vertices in a LINE can be any number, we need to create a list
		vertices = []
		#Returns a list of vertex information (another list)
		vertices.append(VERTEX(entity.dxf.start))
		vertices.append(VERTEX(entity.dxf.end))
		raw_vertices = copy.deepcopy(vertices)
		self.vertices = raw_vertices
		self.zeroed_vertices = zero_and_round(vertices)
		self.layer = entity.dxf.layer
		self.handle = entity.dxf.handle
		self.type = entity.dxftype()

class ARC:
	def __init__(self, entity):
		#As the amount of vertices in a LINE can be any number, we need to create a list
		vertices = []
		#Returns a list of vertex information (another list)
		vertices.append(VERTEX(entity.dxf.center))

		raw_vertices = copy.deepcopy(vertices)
		self.vertices = raw_vertices
		self.zeroed_vertices = zero_and_round(vertices)
		self.radius = entity.dxf.radius
		self.startangle = entity.dxf.start_angle
		self.endangle = entity.dxf.end_angle
		self.layer = entity.dxf.layer
		self.handle = entity.dxf.handle
		self.type = entity.dxftype()

class CIRCLE:
	def __init__(self, entity):
		#As the amount of vertices in a LINE can be any number, we need to create a list
		vertices = []
		#Returns a list of vertex information (another list)
		vertices.append(VERTEX(entity.dxf.center))

		raw_vertices = copy.deepcopy(vertices)
		self.vertices = raw_vertices
		self.zeroed_vertices = zero_and_round(vertices)
		self.radius = entity.dxf.radius
		self.layer = entity.dxf.layer
		self.handle = entity.dxf.handle
		self.type = entity.dxftype()

class MTEXT:
	def __init__(self, entity):
		#As the amount of vertices in a LINE can be any number, we need to create a list
		vertices = []
		#Returns a list of vertex information (another list)
		vertices.append(VERTEX(entity.dxf.insert))

		raw_vertices = copy.deepcopy(vertices)
		self.vertices = raw_vertices
		self.zeroed_vertices = zero_and_round(vertices)
		self.charheight = entity.dxf.char_height
		self.width = entity.dxf.width
		self.text = entity.get_text()
		self.layer = entity.dxf.layer
		self.handle = entity.dxf.handle
		self.type = entity.dxftype()

class BASE_ENTITY:
	def __init__(self, entity):
		self.layer = entity.dxf.layer
		self.handle = entity.dxf.handle
		self.type = entity.dxftype()

class INSERT:
	def __init__(self, entity):
		for attrib in entity.attribs():
			self.ID = attrib.dxf.text
		self.name = entity.dxf.name
		self.rotation = entity.dxf.rotation
		self.xscale = entity.dxf.xscale
		self.yscale = entity.dxf.yscale
		self.zscale = entity.dxf.zscale
		self.xpoint = entity.dxf.insert[0] 
		self.ypoint = entity.dxf.insert[1] 
		self.zpoint = entity.dxf.insert[2]
		self.rowcount = entity.dxf.row_count
		self.rowspacing = entity.dxf.row_spacing
		self.columncount = entity.dxf.column_count
		self.columnspacing = entity.dxf.column_spacing
		self.layer = entity.dxf.layer


class BLOCK:
	def __init__(self, block_ref):
		self.name = block_ref.name
		#List for the types of entity in this block
		self.types = []
		#Initialize the numbers of each attribute for reporting
		self.numlwpolylines = 0
		self.numlines = 0
		self.numcircles = 0
		self.numarcs = 0
		self.nummtexts = 0
		#Go through each type of block entity and add them to lists of their type
		#Define the tag and prompt attributes from the ATTDEF blockentity
		for block_entity in block_ref:
			if block_entity.dxftype() == "LWPOLYLINE":
				if "lwpolylines" not in self.types:
					self.types.append("lwpolylines")
					self.lwpolylines = []
				self.lwpolylines.append(LWPOLYLINE(block_entity))
				self.numlwpolylines = len(self.lwpolylines)
			elif block_entity.dxftype() == "LINE":
				if "lines" not in self.types:
					self.types.append("lines")
					self.lines = []
				self.lines.append(LINE(block_entity))
				self.numlines = len(self.lines)
			elif block_entity.dxftype() == "ARC":
				if "arcs" not in self.types:
					self.types.append("arcs")
					self.arcs = []
				self.arcs.append(ARC(block_entity))
				self.numarcs = len(self.arcs)
			elif block_entity.dxftype() == "CIRCLE":
				if "circles" not in self.types:
					self.types.append("circles")
					self.circles = []
				self.circles.append(CIRCLE(block_entity))
				self.numcircles = len(self.circles)
			elif block_entity.dxftype() == "MTEXT":
				if "mtexts" not in self.types:
					self.types.append("mtexts")
					self.mtexts = []
				self.mtexts.append(MTEXT(block_entity))
				self.nummtexts = len(self.mtexts)	
			elif block_entity.dxftype() == "ATTDEF":
				if "attdef" not in self.types:
					self.types.append("attdef")
				self.tag = block_entity.dxf.tag
				self.prompt = block_entity.dxf.prompt
				self.numattdef = "N/A"


def insertcoord_shift(insert_dict):
	x_coords = []
	y_coords = []
	shifted_dict = insert_dict
	for value in shifted_dict.values():
		#dig into the first and second entries of the embedded coordinate list to get the x and y coordinates
		x_coords.append(value.xpoint)
		y_coords.append(value.ypoint)
	#For each entry in these x or y coordinate lists, increase them by the absolute value of the lowest negative number
	#This zeroes the coordinate system. Then round them to 3 decimal places. 
	#Only do this if the lowest number in the x or y coordinate list is a negative!
	shiftx_coords = [round(x + abs(min(x_coords)), 3) if min(x_coords) < 0 else round(x, 3) for x in x_coords]
	shifty_coords = [round(y + abs(min(y_coords)), 3) if min(y_coords) < 0 else round(y, 3) for y in y_coords]
	#Update the shifted coordinates
	for counter, value in enumerate(shifted_dict.values()):
		#update the rounded and shifted coordinates
		value.xpoint = shiftx_coords[counter]
		value.ypoint = shifty_coords[counter]
	return shifted_dict

def create_csv(shifted_dict, block_dict, base_entity_dict, dxffile):
	with open(os.path.splitext(dxffile)[0] + ".csv", "w", newline='') as csv_file:
		writer = csv.writer(csv_file, delimiter=',')
		title = ["Insert ID", "Assigned Block", "Layer", "Coordinates", "Handles of LWPolylines and Circles", "Number of LWPolylines", "Number of Lines", "Number of Circles", "Number of Arcs", "Number of MTexts"]
		writer.writerow(title)
		for insert in shifted_dict.values():
			coords = f"({insert.xpoint}, {insert.ypoint})"
			handle = []
			if 'lwpolylines' in block_dict[insert.name].types:
				for lw in block_dict[insert.name].lwpolylines: 
					handle.append(lw.handle)
			elif 'circles' in block_dict[insert.name].types:
				for c in block_dict[insert.name].circles: 
					handle.append(c.handle)
			else:
				handle.append("N/A")
			handle_str = ''.join(str(e) for e in handle)
			info_line = [insert.ID, insert.name, insert.layer, coords, handle_str, block_dict[insert.name].numlwpolylines, block_dict[insert.name].numlines, block_dict[insert.name].numcircles, block_dict[insert.name].numarcs, block_dict[insert.name].nummtexts]
			writer.writerow(info_line)

		other_ent_title = ["Type", "Handle", "Layer", "Coordinates"]
		writer.writerow(other_ent_title)
		for entity in base_entity_dict.values():
			coords = f"({entity.vertices[0].xpoint}, {entity.vertices[0].ypoint})"
			info_line = [entity.type, entity.handle, entity.layer, coords]
			writer.writerow(info_line)

	return None







	

