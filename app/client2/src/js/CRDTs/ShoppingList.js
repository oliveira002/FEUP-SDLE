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

    static merge(a, b){
        let items = Array.from(a.items.keys()).concat(Array.from(b.items.keys()))
        const uniqueItems = new Set(items);

        let mergedItems = new Map()
        for (const item of uniqueItems) {
            mergedItems.set(item,
                PNCounter.merge(
                    (a.items.get(item) ?? PNCounter.zero()),
                    (b.items.get(item) ?? PNCounter.zero())
                )
            );
        }

        // Assuming a.uuid === b.uuid
        let mergedSL = new ShoppingList(a.uuid)
        mergedSL.items = mergedItems
        return mergedSL
    }

    toString(){
        let items = Array.from(this.items.entries()).map(([key, value]) => `"${key}": {${value.toString()}}`);
        return "{\"uuid\":\"" + this.uuid + "\", \"items\": {" + items + "}}"
    }


}

module.exports = ShoppingList