from fastapi import FastAPI, HTTPException
import json
from pydantic import BaseModel


class Item(BaseModel):
	id: int
	name: str

json_filename="menu.json"

with open(json_filename,"r") as read_file:
	data = json.load(read_file)

app = FastAPI()

@app.get('/menu')
async def read_all_menu():
	return data['menu']


@app.get('/menu/{item_id}')
async def read_menu(item_id: int):
	for menu_item in data['menu']:
		if menu_item['id'] == item_id:
			return menu_item
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)

@app.post('/menu')
async def add_menu(item: Item):
	item_dict = item.dict()
	item_found = False
	for menu_item in data['menu']:
		if menu_item['id'] == item_dict['id']:
			item_found = True
			return "Menu ID "+str(item_dict['id'])+" exists."
	
	if not item_found:
		data['menu'].append(item_dict)
		with open(json_filename,"w") as write_file:
			json.dump(data, write_file)

		return item_dict
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)

@app.patch('/menu')
async def update_menu(item: Item):
	item_dict = item.dict()
	item_found = False
	for menu_idx, menu_item in enumerate(data['menu']):
		if menu_item['id'] == item_dict['id']:
			item_found = True
			data['menu'][menu_idx]=item_dict
			
			with open(json_filename,"w") as write_file:
				json.dump(data, write_file)
			return "updated"
	
	if not item_found:
		return "Menu ID not found."
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)

@app.delete('/menu/{item_id}')
async def delete_menu(item_id: int):

	item_found = False
	for menu_idx, menu_item in enumerate(data['menu']):
		if menu_item['id'] == item_id:
			item_found = True
			data['menu'].pop(menu_idx)
			
			with open(json_filename,"w") as write_file:
				json.dump(data, write_file)
			return "updated"
	
	if not item_found:
		return "Menu ID not found."
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)