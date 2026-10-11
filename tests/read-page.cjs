// JSDOM runs the same initializer with generated public JSON hydrated locally.
const fs=require('node:fs'),path=require('node:path');
module.exports=name=>fs.readFileSync(name,'utf8').replace(/await loadPublicData\('([^']+)'\)/g,(_,file)=>'JSON.parse('+JSON.stringify(fs.readFileSync(path.resolve(__dirname,'..',file),'utf8')).replaceAll('<','\\u003c')+')');
