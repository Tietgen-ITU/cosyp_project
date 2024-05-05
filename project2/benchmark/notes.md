Some interesting cases I found during random query generation.

Very large difference in time taken for the same query in Postgres and Elasticsearch. And the resulting articles are wildly different. Why?

```
1) Postgres results for 'archive date' (5.86s)
   0.9999997 | Academy Awards
   0.9999997 | Apollo 11
   0.9999997 | Alabama
   0.9999997 | Amsterdam
   0.9999997 | Algeria

1) Elasticsearch results for 'archive date' (0.09s)
   2.168205 | Greek cuisine
   2.167736 | 1988
   2.167273 | March 8
   2.1665473 | February 25
   2.1665282 | February 8
```
