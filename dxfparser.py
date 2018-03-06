import ezdxf
from entityprocessor import *


dxffile = "Test.dxf"

#parsed_dxf is a Drawing object in ezdxf
parsed_dxf = ezdxf.readfile(dxffile)

modelspace = parsed_dxf.modelspace()
layers = parsed_dxf.layers

#Iterate through the Block space and extract the Entities within them
#First go through each block within the dxf file
block_dict = {}
for block_ref in parsed_dxf.blocks:
	new_block_key = block_ref.name
	block_dict[new_block_key] = BLOCK(block_ref)

#Assign INSERT entities to a dictionary and initialize their objects
insert_dict = {}
base_entity_dict = {}
for entity in modelspace:
	if entity.dxftype() == "INSERT":
		for attrib in entity.attribs():
			INSERT_ID = attrib.dxf.text
			insert_dict[INSERT_ID] = INSERT(entity)
	elif entity.dxftype() == "LWPOLYLINE":
		base_entity_dict[entity.dxf.handle] = LWPOLYLINE(entity)
	elif entity.dxftype() == "LINE":
		base_entity_dict[entity.dxf.handle] = LINE(entity)
	elif entity.dxftype() == "MTEXT":
		base_entity_dict[entity.dxf.handle] = MTEXT(entity)
	elif entity.dxftype() == "CIRCLE":
		base_entity_dict[entity.dxf.handle] = CIRCLE(entity)
	elif entity.dxftype() == "ARC":
		base_entity_dict[entity.dxf.handle] = ARC(entity)
	else:
		print(entity.dxftype())
		base_entity_dict[entity.dxf.handle] = BASE_ENTITY(entity)

create_csv(insert_dict, block_dict, base_entity_dict, dxffile)
print("CSV created successfully.")

