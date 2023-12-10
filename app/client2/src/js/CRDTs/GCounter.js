class GCounter {
    constructor(counter) {
        this.counter = counter
    }

    static zero() {
        return new GCounter(new Map())
    }

    value() {
        return Object.values(this.counter).reduce((acc, currentValue) => acc + currentValue, 0);
    }

    inc(replica, value) {
        this.counter.set(replica, (this.counter.get(replica) ?? 0) + value)
    }

    static merge(a, b) {

        let keys = Array.from(a.counter.keys()).concat(Array.from(b.counter.keys()))
        const uniqueKeys = new Set(keys);

        let mergedCounter = new Map()
        for (const k of uniqueKeys) {
            mergedCounter.set(k,
                Math.max(
                    (a.counter.get(k) ?? 0),
                    (b.counter.get(k) ?? 0)
                )
            );
        }
        return new GCounter(mergedCounter);
    }

    toString() {
        const entries = Array.from(this.counter.entries()).map(([key, value]) => `"${key}": ${value}`);
        return `{ ${entries.join(', ')} }`;
    }

}

module.exports = GCounter