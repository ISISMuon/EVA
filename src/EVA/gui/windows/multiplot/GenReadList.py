def GenReadList(line):
    #decodes the Table
    RunList = []

    for i in range(len(line)):
        #print(i, line[i][0])
        start = line[i][0]
        end = line[i][1]
        step = line[i][2]

        if start != 0:

            if end == 0:
                RunList.append(str(line[i][0]))
            else:
                if step == 0:
                    RunList.append(start)
                    RunList.append(end)
                else:
                    for j in range(start,end+1,step):
                        RunList.append(str(j))
    return RunList


