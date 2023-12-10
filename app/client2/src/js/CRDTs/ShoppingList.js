const { v4: uuidv4 } = require('uuid');
const PNCounter = require("./PNCounter");

class ShoppingList{
    constructor(uuid=null) {
        this.items = new Map()
        this.uuid = uuidv4()
        if(uuid !== null) {
            this.uuid = uuid
        }
    }

    inc_or_add_item(item_name, quantity, replica){
        let item =  this.items.get(item_name) ?? PNCounter.zero()
        item.inc(replica, quantity)
        this.items.set(item_name, item)
    }

    dec_item(item_name, quantity, replica){
        let item =  this.items.get(item_name) ?? PNCounter.zero()
        item.dec(replica, quantity)
        this.items.set(item_name, item)
    }

    toString(){
        let items = Array.from(this.items.entries()).map(([key, value]) => `"${key}": {${value.toString()}}`);
        return "{\"uuid\":\"" + this.uuid + "\", \"items\": {" + items + "}}"
    }

}

module.exports = ShoppingList