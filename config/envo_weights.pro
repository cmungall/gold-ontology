
% same category boosts probability
weight(1.0, [predicate_id='owl:equivalentClass', subject_category=X, object_category=X]).

% same source less likely to be equivalent
weight(-3, [predicate_id='owl:equivalentClass', subject_source=X, object_source=X]).

% xrefs
weight(1.0, [predicate_id='owl:equivalentClass', subject_match_field='oio:hasDbXref', object_match_field='oio:hasDbXref']).

% combos of label/exact
%weight(2.5, [predicate_id='owl:equivalentClass', subject_match_field='rdfs:label', object_match_field='rdfs:label']).
%weight(2.0, [predicate_id='owl:equivalentClass', subject_match_field='oio:hasExactSynonym', object_match_field='rdfs:label']).
%weight(2.0, [predicate_id='owl:equivalentClass', subject_match_field='oio:hasExactSynonym', object_match_field='oio:hasExactSynonym']).
%weight(2.0, [predicate_id='owl:equivalentClass', subject_match_field='rdfs:label', object_match_field='oio:hasExactSynonym']).

weight(2, [predicate_id='owl:equivalentClass', any_match_field='dc:identifier']).
weight(2, [predicate_id='owl:equivalentClass', any_match_field='schema:url']).

weight(1.2, [predicate_id='owl:equivalentClass', any_match_field='rdfs:label']).
weight(1.0, [predicate_id='owl:equivalentClass', any_match_field='oio:hasExactSynonym']).
weight(1.0, [predicate_id='owl:equivalentClass', any_match_field='skos:exactMatch']).

weight(-1, [predicate_id='owl:equivalentClass', any_match_field='oio:hasNarrowSynonym']).
weight(-1, [predicate_id='owl:equivalentClass', any_match_field='oio:hasBroadSynonym']).

weight(-2, [predicate_id='owl:equivalentClass', object_source='ENVO', any_match_field='oio:hasRelatedSynonym']).

% lexical is lower, stemmming even lower
weight(-2.0, [predicate_id='owl:equivalentClass', match_type=['Lexical','Flattening']]).
weight(-1.0, [predicate_id='owl:equivalentClass', match_type=['Lexical','Stemming']]).
weight(-0.5, [predicate_id='owl:equivalentClass', match_type=['Lexical']]).

weight(-1, [match_string=S]) :-  atom_length(S,3).
weight(-2, [match_string=S]) :-  atom_length(S,2).
weight(-3, [match_string=S]) :-  atom_length(S,1).
weight(-99, [match_string=S]) :-  atom_length(S,0).

weight(1, [subject_category='gold.path:Environmental', object_source='ENVO']).
weight(2, [subject_category='gold.path:Host-associated', object_source='UBERON']).
weight(2, [subject_category='gold.path:Host-associated', object_source='PO']).
weight(2, [subject_category='gold.path:Host-associated', object_source='NCBITaxon']).
