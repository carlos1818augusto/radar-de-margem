function scenario(price, cost, discount, units) {
  if (![price,cost,discount,units].every(Number.isFinite) || price<0 || cost<0 || units<0 || discount<0 || discount>100) throw new Error('Premissas inválidas');
  const revenue=Math.round(Math.round(units*(1-discount/100))*price*100)/100;
  const totalCost=Math.round(units*cost*100)/100;
  return {revenue,cost:totalCost,profit:revenue-totalCost,margin:revenue? (revenue-totalCost)/revenue:null,breakEven:discount<100?cost/(1-discount/100):null};
}
if(typeof module!=='undefined')module.exports=scenario;
