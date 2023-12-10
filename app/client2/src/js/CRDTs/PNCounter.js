const GCounter = require("./GCounter");

class PNCounter{
    constructor(pos, neg) {
        this.pos = pos
        this.neg = neg
    }

    static zero() {
        return new PNCounter(GCounter.zero(), GCounter.zero())
    }

    value(){
        return this.pos.value() - this.neg.value()
    }

    inc(replica, value){
        this.pos.inc(replica, value)
    }

    dec(replica, value){
        this.neg.inc(replica, value)
    }
    static merge(a, b){
        return new PNCounter(GCounter.merge(a.pos, b.pos), GCounter.merge(a.neg, b.neg))
    }

    toString(){
        return "\"pos\":" + this.pos.toString() + ", \"neg\":" + this.neg.toString()
    }

}

module.exports = PNCounter