

class Namespace(object):
    '''
    Used to quickly create a Namespace.
    '''

    def __init__(self, **kwargs):
        '''
        Constructs the Namespace. The name of 
        each field must be specified along with
        an assigned value.
        '''

        for field, value in kwargs.items():
            setattr(self, field, value)

    def __str__(self):
        '''
        Represent the Namespace as a string.
        '''

        indat = "".join("({}={})".format(field, value) for field, value in vars(self).items())
        full  = "{}({})".format(self.__class__.__name__,indat)
        return full

    def issubsetof(self, namespace):
        '''
        Determines whether or not this namespace is a subset of the specified namespace. 
        '''
        return all( hasattr(namespace, mem) and getattr(namespace, mem)==val for mem, val in vars(self).items() )

    def isequalto(self, namespace):
        '''
        Determines whether or not this namespace is equal to the specified namespace.
        '''
        return self.issubsetof(namespace) and (self.size()==namespace.size())

    def size(self):
        '''
        Returns the number of members in the namespace.
        '''        
        return len(vars(self))

    def __eq__(self, namespace):
        '''
        Determines whether or not this namespace is equal to the specified namespace.
        '''
        return self.isequalto(namespace)

class Transaction(Namespace):
    '''
    Used to quickly create a Transaction, which
    is used in a lot of the cocotb high-level operations.
    '''
    pass

class Interface(Namespace):
    '''
    Represents a group of cocotb handles.
    '''    
    _cntrl = []

    def transaction(self, **data):
        '''
        Generates a transaction whose members 
        are only the data signals.
        '''
        trans = {}
        for name, handle in vars(self).items():
            if name is not self._cntrl:
                trans[name] = getattr(data, name, None)
        return Transaction(**trans)                

