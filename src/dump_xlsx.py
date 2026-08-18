import sys, openpyxl
p=sys.argv[1]
maxr=int(sys.argv[2]) if len(sys.argv)>2 else 30
wb=openpyxl.load_workbook(p, data_only=True)
for ws in wb.worksheets:
    print(f"### LIST: {ws.title}  dims={ws.dimensions} max_row={ws.max_row} max_col={ws.max_column}")
    for i,row in enumerate(ws.iter_rows(values_only=True),1):
        if i>maxr: print("   ... (zkraceno)"); break
        cells=[('' if c is None else str(c).replace('\n',' ')) for c in row]
        while cells and cells[-1]=='': cells.pop()
        if cells: print(f"{i:>4}: " + ' | '.join(cells))
    print()
