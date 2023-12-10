const GCounter = require("./GCounter.js");
const PNCounter = require("./PNCounter");
const ShoppingList = require("./ShoppingList");


function main(){

    let gc = GCounter.zero()
    gc.inc("5fb2f941-0c40-4aef-b48f-746540e3c723", 5)
    gc.inc("5fb2f941-0c40-4aef-b48f-746540e3c723", 5)
    gc.inc("263bf63c-b5fd-4beb-95c5-396f14167ee0", 2)
    //console.log(gc.toString())

    let map = {"5fb2f941-0c40-4aef-b48f-746540e3c723": 8, "263bf63c-b5fd-4beb-95c5-396f14167ee0": 3}
    let gc2 = new GCounter(new Map(Object.entries(map)))
    let gc3 = GCounter.merge(gc, gc2)
    gc3 = GCounter.merge(gc3, gc2)
    //console.log(gc3.toString())

    let pn = new PNCounter(gc, gc2)
    //console.log(pn.toString())

    let sl = new ShoppingList()
    let replica = "5fb2f941-0c40-4aef-b48f-746540e3c723"
    sl.inc_or_add_item("banana", 8, replica)
    sl.inc_or_add_item("cebolas", 4, replica)
    sl.dec_item("banana", 2, replica)
    console.log(sl.toString())

} main()