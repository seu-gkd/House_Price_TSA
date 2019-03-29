if __name__ == '__main__':
    with open('error.txt','r',encoding='utf-8') as f:
        data = f.read().split('\n')
    count = len(data)
    error = 0.0
    for item in data:
        # if '->' in item:
        #     continue
        if item.split(':')[1] == 'error':
            continue
        error += float(item.split(':')[1])
    a = 0
