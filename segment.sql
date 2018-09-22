-- need spatial index and primary key (unlinks and network layer)

-- example

SELECT functions_ssx.segment(
  'p0000.axial_map_m25',
  'p0000.axial_map_m25_u'
);

-- todo: add unlink_buffer?
DROP FUNCTION IF EXISTS functions_ssx.segment(text, text, numeric, boolean);
CREATE OR REPLACE FUNCTION functions_ssx.segment(
  network_layer text, -- layer to get the values from
  unlinks_layer text,  -- filter specific features
  stub_ratio numeric DEFAULT 0.4, -- aggregation type used for the percentage calculation
  merge_colinear boolean DEFAULT FALSE
)

RETURNS VOID AS
$FUNC$
DECLARE
 sql text;
 _pkey text;
 _unkey text;
 srid text;
 segment_layer text;
 segment_layer_name text;
 index_name text;
BEGIN

  --find srid
  sql :=  'SELECT ST_SRID(geom) FROM ' || network_layer || ' LIMIT 1;';
  EXECUTE sql INTO srid;
  RAISE NOTICE 'identified srid: %', srid;

  -- find layer primary key - network
  sql :=  'SELECT a.attname
          FROM   pg_index i
            JOIN   pg_attribute a ON a.attrelid = i.indrelid  AND a.attnum = ANY(i.indkey)
          WHERE  i.indrelid = $1::regclass AND i.indisprimary;';
  EXECUTE sql INTO _pkey USING network_layer;

  -- find layer primary key - unlinks
  sql :=  'SELECT a.attname
          FROM   pg_index i
            JOIN   pg_attribute a ON a.attrelid = i.indrelid  AND a.attnum = ANY(i.indkey)
          WHERE  i.indrelid = $1::regclass AND i.indisprimary;';
  EXECUTE sql INTO _unkey USING unlinks_layer;

  -- specify segment_layer
  sql := 'SELECT $1||''_seg'';';
  EXECUTE sql INTO segment_layer USING network_layer;
  RAISE NOTICE 'identified segment_layer_name: %', segment_layer;

  -- specify segment_layer
  sql := 'SELECT right($1, length($1)- strpos($1, ''.''));';
  EXECUTE sql INTO segment_layer_name USING segment_layer;
  RAISE NOTICE 'identified segment_layer_name: %', segment_layer_name;

  -- sepcify nodes_layer_index_name
  sql := 'SELECT $1||''_gix'';';
  EXECUTE sql INTO index_name USING segment_layer_name;
  RAISE NOTICE 'specified index_name: %', index_name;

  -- create segment table
  sql := 'CREATE TABLE '||segment_layer||' (
          segm_id serial PRIMARY KEY,
          '||_pkey||' bigint,
          geom geometry(linestring, '||srid||'));
          CREATE INDEX '||index_name||' ON '||segment_layer||' USING GIST (geom);';
  EXECUTE sql;
  RAISE NOTICE 'created segment layer';

  -- add segments
  sql := '
  WITH b AS (SELECT net.'||_pkey||', cross_lines.cr_line_id AS cross_line
            FROM '||network_layer||' AS net
            CROSS JOIN LATERAL (SELECT net2.'||_pkey||' AS cr_line_id
            									FROM '||network_layer||' AS net2
            									WHERE ST_DWithin(net.geom, net2.geom, 0.0000000000000000000000001)  AND net.'||_pkey||' <> net2.'||_pkey||') cross_lines
            EXCEPT
            SELECT *
            FROM (WITH a AS (
                  SELECT array_agg(unlinked_id) AS info
                  FROM  '||unlinks_layer||' AS unlinks
                  CROSS JOIN LATERAL
                  (SELECT net.'||_pkey||' AS unlinked_id
                  FROM '||network_layer||' AS net
                  WHERE ST_DWithin(net.geom, unlinks.geom, 0.0000000000000000000000001)) unlinks_info
                  GROUP  BY unlinks.'||_unkey||'
                  )
                  SELECT info[1] AS line1, info[2] AS line2
                  FROM a
                  UNION
                  SELECT info[2] AS line1, info[1] AS line2
                  FROM a
                ) oti),

  cross_points AS (SELECT b.'||_pkey||', net1.geom, ST_ClosestPoint(net1.geom, net2.geom) AS cross_p
        					FROM b, '||network_layer||' AS net1, '||network_layer||' AS net2
        					WHERE net2.'||_pkey||' = b.cross_line AND net1.'||_pkey||' = b.'||_pkey||'
        					--AND b.id = 1830
        					UNION
        					SELECT net3.'||_pkey||', net3.geom, (ST_DumpPoints(net3.geom)).geom AS cross_p
        					FROM '||network_layer||' AS net3
        					--WHERE net3.id = 1830
                  ),
  cross_points_grouped AS (SELECT id, geom, ST_Collect(cross_p) AS blade
        									FROM cross_points
        									GROUP BY id, geom)
  INSERT INTO '||segment_layer||'('||_pkey||', geom)
  -- TODO force output of ST_Split to be linestring
  SELECT cr.'||_pkey||', (ST_Dump(ST_Split(ST_Snap(cr.geom, cr.blade, 0.00001), cr.blade))).geom
  FROM cross_points_grouped AS cr
  ;';
  EXECUTE sql;
  RAISE NOTICE 'segmentation finished';

  -- delete stubs
  IF $3 <> 0
  THEN

  sql := ' WITH dead_end_p AS (SELECT endp, segm_ids[1] AS segm_id
                              FROM (SELECT array_agg(segm_id) segm_ids, endp, count(id)
                                    FROM (SELECT segm_id, id, ST_StartPoint(geom) endp FROM '||segment_layer||'
                                          UNION
                                          SELECT segm_id, id, ST_EndPoint(geom) endp FROM '||segment_layer||') a
                                    GROUP BY endp) b
                              WHERE count = 1)
  DELETE FROM '||segment_layer||' segms
  USING '||network_layer||' AS net
  WHERE net.'||_pkey||' = segms.'||_pkey||' AND ST_Length(segms.geom)/ ST_Length(net.geom) <= 0.4 AND segms.segm_id IN (SELECT segm_id FROM dead_end_p);';

  EXECUTE sql;
  RAISE NOTICE 'cleaning stubs finished';

  END IF;
  -- merge collinear

END;
 $FUNC$
 LANGUAGE 'plpgsql' VOLATILE STRICT;
