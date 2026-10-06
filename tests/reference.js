/* 独立的位串实现；不使用 Python 查表优化或中间结果。仅用于交叉测试。 */
'use strict';
const choose = (bits, positions) => positions.map(p => bits[p - 1]).join('');
const xor = (a,b) => [...a].map((bit,i) => bit === b[i] ? '0' : '1').join('');
const rotate = (half,n) => half.slice(n) + half.slice(0,n);
function keys(master) {
  let arranged = choose(master,[3,5,2,7,4,10,1,9,8,6]);
  let left = rotate(arranged.slice(0,5),1), right = rotate(arranged.slice(5),1);
  const first = choose(left+right,[6,3,7,4,8,5,10,9]);
  left = rotate(left,2); right = rotate(right,2);
  return [first,choose(left+right,[6,3,7,4,8,5,10,9])];
}
function round(block,key) {
  const mixed = xor(choose(block.slice(4),[4,1,2,3,2,3,4,1]),key);
  const tables = [[[1,0,3,2],[3,2,1,0],[0,2,1,3],[3,1,0,2]],[[0,1,2,3],[2,3,1,0],[3,0,1,2],[2,1,0,3]]];
  const substituted = [mixed.slice(0,4),mixed.slice(4)].map((part,i) => tables[i][parseInt(part[0]+part[3],2)][parseInt(part.slice(1,3),2)].toString(2).padStart(2,'0')).join('');
  return xor(block.slice(0,4),choose(substituted,[2,4,3,1]))+block.slice(4);
}
function crypt(input,roundKeys) {
  let current = round(choose(input,[2,6,3,1,4,8,5,7]),roundKeys[0]);
  current = current.slice(4)+current.slice(0,4);
  return choose(round(current,roundKeys[1]),[4,1,3,5,7,2,8,6]);
}
module.exports = {keys,crypt};
if(require.main === module) {
  const digest = require('node:crypto').createHash('sha256');
  let checked = 0;
  for(let key=0;key<1024;key++) {
    const roundKeys = keys(key.toString(2).padStart(10,'0'));
    for(let plain=0;plain<256;plain++) {
      const input = plain.toString(2).padStart(8,'0');
      const cipher = crypt(input,roundKeys);
      if(crypt(cipher,[...roundKeys].reverse()) !== input) throw new Error('JS decrypt roundtrip failed');
      digest.update(Buffer.from([parseInt(cipher,2)])); checked++;
    }
  }
  console.log(JSON.stringify({checked,sha256:digest.digest('hex'),runtime:process.version}));
}
