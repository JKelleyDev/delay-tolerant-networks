class Emitter {
    constructor() { this.map = new Map(); }
    on(type, cb) {
      if (!this.map.has(type)) this.map.set(type, new Set());
      this.map.get(type).add(cb);
      return () => this.map.get(type)?.delete(cb);
    }
    emit(type, payload) {
      const set = this.map.get(type);
      if (!set) return;
      for (const cb of set) cb(payload);
    }
  }
  export const events = new Emitter();