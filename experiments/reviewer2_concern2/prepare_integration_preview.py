"""Create an exact-source review diff for Concerns 2/3, never edit manuscript inputs."""
from pathlib import Path
import difflib
import hashlib
import json

HERE=Path(__file__).resolve().parent
P=HERE/'manuscript_proposals'
P3=HERE.parent/'reviewer2_concern3/manuscript_proposals'
FILES={
    'main (1).tex':'164ecc28146a11bbdde0ffbb5efb5d3f77224fc1ba71e71d26ed1dbb1c6f06f6',
    'supplementary_material (2).tex':'ea4345a3231c0c6a341c85730df3304f8a5eac47e00c2abd2fe639c381bc3dc7',
}

def main():
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    paths={n:Path('C:/Users/isegu/Downloads')/n for n in FILES}
    before={n:sha(p) for n,p in paths.items()}
    assert before==FILES,'Source changed: reread and review insertion anchors first.'
    originals={n:p.read_text(encoding='utf-8') for n,p in paths.items()}
    paper=originals['main (1).tex'];lines=paper.splitlines()
    read=lambda n:(P/n).read_text(encoding='utf-8').strip()
    read3=lambda n:(P3/n).read_text(encoding='utf-8').strip()
    replacements={
        (53,53):read('paper/00_abstract_replacement.tex'),
        (258,258):read('paper/01_demonstration_selection.tex'),
        (284,284):lines[283].replace('All experiments are performed locally','The original 72-configuration experiments were performed locally'),
        (298,298):read3('paper/00_metric_scope.tex'),
        (306,306):read3('paper/02_meaningbert_scope.tex'),
        (308,308):lines[307].replace('Lower FKGL values and higher FRE scores indicate simpler and more readable texts.','Lower FKGL values and higher FRE scores indicate lower estimated surface reading difficulty; they do not directly measure comprehension.')+'\n\n'+read3('paper/01_output_descriptors.tex'),
        (310,310):'For the original 72-configuration tables, the following historical paired-comparison protocol and annotations are retained. '+lines[309],
        (315,315):read('paper/02_joint_analysis_methods.tex')+'\n\n'+lines[314]+'\n\n'+read('paper/04_original_results_scope.tex'),
        (561,561):read('paper/05_selection_results.tex')+'\n\n'+read('paper/03_primary_sari_table.tex')+'\n\n'+lines[560],
        (685,687):read('paper/06_RQ1_replacement.tex'),
        (693,693):read('paper/07_RQ2_count_replacement.tex'),
        (695,695):read3('paper/04_discussion_similarity.tex'),
        (700,706):read('paper/08_RQ3_replacement.tex'),
        (710,714):read('paper/09_RQ4_replacement.tex'),
        (718,724):read('paper/12_RQ5_replacement.tex'),
        (747,747):lines[746]+'\n\n'+read('paper/10_selection_limitations.tex'),
        (749,749):lines[748]+' '+read3('paper/03_evaluation_limitations.tex'),
        (769,773):read('paper/11_conclusion_replacement.tex'),
    }
    anchors=[]
    for (start,end),replacement in replacements.items():
        old='\n'.join(lines[start-1:end]);assert paper.count(old)==1,(start,end)
        paper=paper.replace(old,replacement,1)
        anchors.append(dict(start=start,end=end,first_line=lines[start-1]))
    supplement=originals['supplementary_material (2).tex']
    snippets=['00_selection_study_protocol.tex','01_metrics_cochrane.tex','01_metrics_plaba.tex',
              '01_metrics_tsar2025.tex','02_individual_sari_selections.tex',
              '03_three_selection_descriptors.tex','04_secondary_sari_contrasts.tex']
    extra='\n\n'.join(read('supplement/'+n) for n in snippets)+'\n\n'+read3('supplement/00_original_72_descriptors.tex')
    anchor='\\section{Additional Materials}';assert supplement.count(anchor)==1
    supplement=supplement.replace(anchor,extra+'\n\n'+anchor,1)
    diff=[]
    for name,new in [('main (1).tex',paper),('supplementary_material (2).tex',supplement)]:
        diff.extend(difflib.unified_diff(originals[name].splitlines(True),new.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    (P/'concerns2_3_proposed_changes.diff').write_text(''.join(diff),encoding='utf-8')
    assert before=={n:sha(p) for n,p in paths.items()}
    (P/'source_integrity_20261028.json').write_text(json.dumps(dict(source_sha256_before=before,source_sha256_after=before,
        originals_unchanged=True,article_identical_to_previous_copy=True,supplement_preamble_and_title_updated=True,
        proposal_diff_only=True,original_tex_edited=False,original_response_doc_edited=False,
        full_ieee_compilation=False,preview_code_sha256=sha(Path(__file__)),paper_anchors=anchors),indent=2)+'\n',encoding='utf-8')
    print('Prepared review-only diff; manuscript sources unchanged.')

if __name__=='__main__':
    main()
