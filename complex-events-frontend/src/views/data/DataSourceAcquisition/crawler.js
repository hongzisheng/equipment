let currentCrawlUrlAndKeyword = null;
export function setCrawlUrlAndKeywords(data) {
  currentCrawlUrlAndKeyword = data;
  console.log('URL已设置:', data);
}

export function getCrawlUrlAndKeywords() {
  return currentCrawlUrlAndKeyword;
}

let associatedData = null;
export function setAssociatedData(keywords) {
  associatedData = keywords;
  console.log('关键词已设置:', keywords);
}

export function getAssociatedData() {
  return associatedData;
}
