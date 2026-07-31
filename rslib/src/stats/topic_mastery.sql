SELECT c.nid,
  n.tags,
  c.type,
  c.queue,
  c.due,
  cast(c.ivl AS integer),
  c.odue,
  c.odid,
  c.data
FROM cards c
  JOIN notes n ON n.id = c.nid
WHERE n.tags REGEXP ?1